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
	"time"
)

const (
	DbFile = "data.db?_pragma=journal_mode(WAL)&_pragma=_synchronous(NORMAL)"

	AuthCookieName = "auth"
	TokenCtxName   = "token"
	UserIdCtxName  = "userId"

	ListTake       = 30
	MaxRoutePlaces = 10
	MaxFieldLength = 128

	ErrorInvalidPlace    = "invalid place"
	ErrorInvalidRoute    = "invalid route"
	ErrorUnauthorized    = "token not found or invalid"
	ErrorUpdateForbidden = "you can only change your own places"
)

var key = []byte(`1234567890abcdef`)
var JwtSecret = []byte("secret")

var db *gorm.DB

func main() {
	var err error

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
	e.Use(middleware.StaticWithConfig(middleware.StaticConfig{
		Root:   "wwwroot",
		Browse: true,
	}))
	e.Use(middleware.TimeoutWithConfig(middleware.TimeoutConfig{
		Timeout: 10 * time.Second,
	}))

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
		r.PUT("/place", put)
		r.PUT("/place/:id", put)
		r.GET("/place/:id", get)
		r.POST("/route", route)
	}

	if err := e.Start("127.0.0.1:8080"); !errors.Is(err, http.ErrServerClosed) {
		panic(err)
	}
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
		if placeId, err := PlaceIdFromString(id, key); err == nil {
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

	placeId, err := PlaceIdFromString(id, key)
	if err != nil {
		return c.String(http.StatusBadRequest, ErrorInvalidPlace)
	}

	data := PlaceData{Id: id}
	if result := db.Find(&data); result.Error != nil {
		return err
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
		placeId, err := PlaceIdFromString(id, key)
		if err != nil {
			return c.String(http.StatusBadRequest, ErrorInvalidPlace)
		}

		if placeId.UserId != userId {
			return c.String(http.StatusForbidden, ErrorUpdateForbidden)
		}

		place.Long = placeId.Long
		place.Lat = placeId.Lat
	}

	id, err := PlaceId{UserId: userId, Long: place.Long, Lat: place.Lat}.ToString(key)
	if err != nil {
		return err
	}

	db.Clauses(clause.OnConflict{UpdateAll: true}).Create(&PlaceData{
		Id:      id,
		Public:  place.Public,
		Secret:  place.Secret,
		Updated: time.Now(),
	})

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
			placeId, e := PlaceIdFromString(item, key)
			if e != nil {
				err = e
			}
			return placeId
		}).
		WhereT(func(item PlaceId) bool {
			return item != PlaceId{}
		}).
		Distinct().
		ToSlice(&route)
	if err != nil {
		return c.String(http.StatusBadRequest, ErrorInvalidRoute)
	}

	var saved []PlaceData
	result := db.Order("Id asc").Find(&saved, places)
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
	id, err := placeId.ToString(key)
	if err != nil {
		return err
	}

	return c.String(http.StatusOK, id)
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
