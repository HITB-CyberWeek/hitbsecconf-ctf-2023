package main

import (
	"encoding/json"
	"errors"
	"github.com/ahmetb/go-linq/v3"
	"github.com/glebarez/sqlite"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	echojwt "github.com/labstack/echo-jwt/v4"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

const (
	DbFile = "data/places.db?_pragma=journal_mode(WAL)&_pragma=_synchronous(NORMAL)"

	AuthCookieName = "auth"
	TokenCtxName   = "token"
	UserIdCtxName  = "userId"

	ListTake       = 30
	MaxRoutePlaces = 10
	MaxFieldLength = 64

	ErrorInvalidPlace    = "invalid place"
	ErrorInvalidRoute    = "invalid route"
	ErrorUnauthorized    = "token not found or invalid"
	ErrorUpdateForbidden = "you can only change your own places"
)

var (
	EncryptionKey = LoadOrCreateKey("settings/enc.key", 16)
	JwtSecret     = LoadOrCreateKey("settings/jwt.key", 16)
	db            *gorm.DB
)

func main() {
	var err error

	err = os.Mkdir(filepath.Dir("data/"), 0750)
	if err != nil && !os.IsExist(err) {
		panic(err)
	}

	db, err = gorm.Open(sqlite.Open(DbFile), &gorm.Config{})
	if err != nil {
		panic(err)
	}

	err = db.AutoMigrate(&PlaceData{})
	if err != nil {
		panic(err)
	}

	e := echo.New()
	e.Use(middleware.BodyLimit("1k"))
	e.Use(middleware.StaticWithConfig(middleware.StaticConfig{Root: "wwwroot"}))
	e.Use(middleware.TimeoutWithConfig(middleware.TimeoutConfig{Timeout: 10 * time.Second}))

	r := e.Group("/api")
	{
		r.Use(echojwt.WithConfig(echojwt.Config{
			SigningKey:    JwtSecret,
			SigningMethod: jwt.SigningMethodHS256.Name,
			TokenLookup:   "cookie:" + AuthCookieName,
			ContextKey:    TokenCtxName,
			ErrorHandler: func(c echo.Context, err error) error {
				return nil
			},
			SuccessHandler: func(c echo.Context) {
				if subject, err := c.Get(TokenCtxName).(*jwt.Token).Claims.(jwt.MapClaims).GetSubject(); err == nil {
					if userId, err := uuid.Parse(subject); err == nil {
						c.Set(UserIdCtxName, userId)
						return
					}
				}
			},
			ContinueOnIgnoredError: true,
		}))

		r.GET("/auth", auth)
		r.GET("/list", list)
		r.PUT("/put/place", put)
		r.PUT("/put/place/:id", put)
		r.GET("/get/place/:id", get)
		r.POST("/route", route)
	}

	if err := e.Start(":8080"); !errors.Is(err, http.ErrServerClosed) {
		panic(err)
	}
}

func auth(c echo.Context) error {
	userId, ok := c.Get(UserIdCtxName).(uuid.UUID)
	if !ok {
		userId = uuid.New()
		signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.RegisteredClaims{Subject: userId.String()}).SignedString(JwtSecret)
		if err != nil {
			return err
		}

		cookie := new(http.Cookie)
		cookie.Name = AuthCookieName
		cookie.Value = signed
		cookie.HttpOnly = true
		cookie.SameSite = http.SameSiteStrictMode
		c.SetCookie(cookie)
	}

	var coords Coords
	if err := c.Bind(&coords); err != nil {
		coords = Coords{}
	}

	placeId := PlaceId{UserId: userId, Lat: coords.Lat, Long: coords.Long}
	id, err := placeId.ToString(EncryptionKey)
	if err != nil {
		return err
	}

	return c.String(http.StatusOK, id)
}

func list(c echo.Context) error {
	var places [ListTake]string
	if result := db.Model(&PlaceData{}).Select("Id").Limit(ListTake).Order("Updated desc").Find(&places); result.Error != nil {
		return result.Error
	}

	c.Response().Header().Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	c.Response().WriteHeader(http.StatusOK)
	enc := json.NewEncoder(c.Response())

	linq.From(places).WhereT(func(place string) bool {
		return place != ""
	}).SelectT(func(id string) CoordsWithId {
		if placeId, err := PlaceIdFromString(id, EncryptionKey); err == nil {
			return CoordsWithId{Id: id, Lat: placeId.Lat, Long: placeId.Long}
		}
		return CoordsWithId{}
	}).WhereT(func(coords CoordsWithId) bool {
		return coords.Id != ""
	}).ForEachT(func(coords CoordsWithId) {
		enc.Encode(coords)
	})

	return nil
}

func get(c echo.Context) error {
	userId, ok := c.Get(UserIdCtxName).(uuid.UUID)
	if !ok {
		return c.String(http.StatusUnauthorized, ErrorUnauthorized)
	}

	id := c.Param("id")

	placeId, err := PlaceIdFromString(id, EncryptionKey)
	if err != nil {
		return c.String(http.StatusBadRequest, ErrorInvalidPlace)
	}

	data := PlaceData{Id: id}
	if result := db.Find(&data); result.Error != nil {
		return result.Error
	}

	place := toPlaceInfo(userId, placeId, data)

	return c.JSON(http.StatusOK, place)
}

func put(c echo.Context) error {
	userId, ok := c.Get(UserIdCtxName).(uuid.UUID)
	if !ok {
		return c.String(http.StatusUnauthorized, ErrorUnauthorized)
	}

	var place PlaceInfo
	if err := c.Bind(&place); err != nil || place.Lat < -90 || place.Lat > 90 || place.Long < -180 || place.Long > 180 || len(place.Public) > MaxFieldLength || len(place.Secret) > MaxFieldLength {
		return c.String(http.StatusBadRequest, ErrorInvalidPlace)
	}

	id := c.Param("id")
	if id != "" {
		placeId, err := PlaceIdFromString(id, EncryptionKey)
		if err != nil {
			return c.String(http.StatusBadRequest, ErrorInvalidPlace)
		}

		if placeId.UserId != userId {
			return c.String(http.StatusForbidden, ErrorUpdateForbidden)
		}

		place.Long = placeId.Long
		place.Lat = placeId.Lat
	}

	id, err := PlaceId{UserId: userId, Long: place.Long, Lat: place.Lat}.ToString(EncryptionKey)
	if err != nil {
		return err
	}

	result := db.Clauses(clause.OnConflict{UpdateAll: true}).Create(&PlaceData{
		Id:      id,
		Public:  place.Public,
		Secret:  place.Secret,
		Updated: time.Now(),
	})

	if result.Error != nil {
		return result.Error
	}

	return c.String(http.StatusOK, id)
}

func route(c echo.Context) error {
	userId, ok := c.Get(UserIdCtxName).(uuid.UUID)
	if !ok {
		return c.String(http.StatusUnauthorized, ErrorUnauthorized)
	}

	var places []string
	if err := (&echo.DefaultBinder{}).BindBody(c, &places); err != nil || len(places) > MaxRoutePlaces {
		return c.String(http.StatusBadRequest, ErrorInvalidRoute)
	}

	var err error

	var route []PlaceId
	linq.From(places).
		OrderByT(func(item string) string { return item }).
		SelectT(func(item string) PlaceId {
			placeId, e := PlaceIdFromString(item, EncryptionKey)
			if e != nil {
				err = e
			}
			return placeId
		}).
		Distinct().
		ToSlice(&route)
	if err != nil {
		return c.String(http.StatusBadRequest, ErrorInvalidRoute)
	}

	var saved []PlaceData
	result := db.Order("Id asc").Find(&saved, places)
	if result.Error != nil {
		return result.Error
	}

	if result.RowsAffected != int64(linq.From(places).Distinct().Count()) || len(saved) != len(route) {
		return c.String(http.StatusBadRequest, ErrorInvalidRoute)
	}

	c.Response().Header().Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	c.Response().WriteHeader(http.StatusOK)
	enc := json.NewEncoder(c.Response())

	linq.From(route).ZipT(linq.From(saved), func(placeId PlaceId, data PlaceData) PlaceInfo {
		return toPlaceInfo(userId, placeId, data)
	}).ForEachT(func(item PlaceInfo) {
		enc.Encode(item)
	})

	return nil
}

func toPlaceInfo(userId uuid.UUID, placeId PlaceId, data PlaceData) PlaceInfo {
	var secret string
	if placeId.UserId == userId {
		secret = data.Secret
	} else {
		secret = ""
	}

	return PlaceInfo{
		Lat:    placeId.Lat,
		Long:   placeId.Long,
		Public: data.Public,
		Secret: secret,
	}
}

type PlaceData struct {
	Id      string `gorm:"primarykey;size:64"`
	Public  string
	Secret  string
	Updated time.Time `gorm:"index:,sort:desc"`
}

type Coords struct {
	Lat  float64 `query:"lat"`
	Long float64 `query:"long"`
}

type CoordsWithId struct {
	Id   string  `json:"id"`
	Lat  float64 `json:"lat"`
	Long float64 `json:"long"`
}

type PlaceInfo struct {
	Lat    float64 `json:"lat"`
	Long   float64 `json:"long"`
	Public string  `json:"public"`
	Secret string  `json:"secret"`
}
