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
	DbFile = "data.db"

	AuthCookieName = "auth"
	TokenCtxName   = "token"
	UserIdCtxName  = "userId"
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
				if c.Path() != "/api/auth" {
					return c.String(http.StatusUnauthorized, "token not found or invalid")
				}
				c.Set(UserIdCtxName, uuid.Nil)
				return nil
			},
			SuccessHandler: func(c echo.Context) {
				if subject, err := c.Get(TokenCtxName).(*jwt.Token).Claims.(jwt.MapClaims).GetSubject(); err == nil {
					if userId, err := uuid.Parse(subject); err == nil {
						c.Set(UserIdCtxName, userId)
						return
					}
				}
				c.Set(UserIdCtxName, uuid.Nil)
			},
			ContinueOnIgnoredError: true,
		}))

		r.GET("/auth", auth)
		r.PUT("/place", put)
		r.PUT("/place/:id", put)
		r.GET("/place/:id", get)
		r.POST("/route", route)
	}

	if err := e.Start("127.0.0.1:8080"); !errors.Is(err, http.ErrServerClosed) {
		panic(err)
	}
}

func get(c echo.Context) error {
	id := c.Param("id")

	placeId, err := placeFromString(id, key)
	if err != nil {
		return c.String(http.StatusBadRequest, "invalid place")
	}

	data := PlaceData{Id: id}
	if result := db.Find(&data); result.Error != nil {
		return err
	}

	userId := c.Get(UserIdCtxName).(uuid.UUID)
	place := toPlace(userId, placeId, data)

	return c.JSON(http.StatusOK, place)
}

func put(c echo.Context) error {
	var place Place

	if err := (&echo.DefaultBinder{}).BindBody(c, &place); err != nil {
		return c.String(http.StatusBadRequest, "failed to parse place")
	}

	userId := c.Get(UserIdCtxName).(uuid.UUID)

	id := c.Param("id")
	if id != "" {
		placeId, err := placeFromString(id, key)
		if err != nil {
			return c.String(http.StatusBadRequest, "invalid place")
		}

		if placeId.UserId != userId {
			return c.String(http.StatusForbidden, "you can only change your own places")
		}

		place.Long = placeId.Long
		place.Lat = placeId.Lat
	}

	id, err := PlaceId{UserId: userId, Long: place.Long, Lat: place.Lat}.toString(key)
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
	var places []string
	if err := (&echo.DefaultBinder{}).BindBody(c, &places); err != nil {
		return c.String(http.StatusBadRequest, "failed to parse route")
	}

	var err error

	var route []PlaceId
	linq.From(places).
		OrderByT(func(item string) string { return item }).
		SelectT(func(item string) PlaceId {
			placeId, e := placeFromString(item, key)
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
		return c.String(http.StatusBadRequest, "invalid route")
	}

	var saved []PlaceData
	result := db.Order("Id asc").Find(&saved, places)
	if result.RowsAffected != int64(linq.From(places).Distinct().Count()) || len(saved) != len(route) {
		return c.String(http.StatusBadRequest, "invalid route")
	}

	/*saved := make([]PlaceData, len(route))
	linq.From(places).OrderByT(func(item string) string { return item }).SelectT(func(item string) PlaceData {
		data := PlaceData{Id: item}
		if result := db.Take(&data); result.Error != nil {
			err = result.Error
		}
		return data
	}).ToSlice(&saved)
	if err != nil {
		return c.String(http.StatusBadRequest, "invalid route")
	}*/

	userId := c.Get(UserIdCtxName).(uuid.UUID)

	c.Response().Header().Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	c.Response().WriteHeader(http.StatusOK)
	enc := json.NewEncoder(c.Response())

	linq.From(route).ZipT(linq.From(saved), func(placeId PlaceId, data PlaceData) Place {
		return toPlace(userId, placeId, data)
	}).ForEachT(func(item Place) {
		enc.Encode(item)
	})

	return nil
}

func toPlace(userId uuid.UUID, placeId PlaceId, data PlaceData) Place {
	return Place{
		Lat:    placeId.Lat,
		Long:   placeId.Long,
		Public: data.Public,
		Secret: getSecretIfOwned(userId, placeId, data.Secret),
	}
}

func getSecretIfOwned(userId uuid.UUID, placeId PlaceId, secret string) string {
	if placeId.UserId == userId {
		return secret
	}
	return ""
}

func auth(c echo.Context) error {
	userId := c.Get(UserIdCtxName).(uuid.UUID)
	if userId == uuid.Nil {
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
	id, err := placeId.toString(key)
	if err != nil {
		return err
	}

	return c.String(http.StatusOK, id)
}

type Coords struct {
	Lat  float64 `query:"lat"`
	Long float64 `query:"long"`
}

type Place struct {
	Long   float64 `json:"long"`
	Lat    float64 `json:"lat"`
	Public string  `json:"public"`
	Secret string  `json:"secret"`
}
