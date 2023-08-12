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
			SuccessHandler: func(c echo.Context) {
				if subject, err := c.Get(TokenCtxName).(*jwt.Token).Claims.(jwt.MapClaims).GetSubject(); err == nil {
					if userId, err := uuid.Parse(subject); err == nil {
						c.Set(UserIdCtxName, userId)
						return
					}
				}
				c.Set(UserIdCtxName, uuid.UUID{})
			},
			ContextKey: TokenCtxName,
		}))

		r.PUT("/place", put)
		r.PUT("/place/:id", put)
		r.GET("/place/:id", get)
		r.POST("/route", route)
	}

	e.PUT("/user", login)

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
	info := toPlaceInfo(userId, placeId, data)

	return c.JSON(http.StatusOK, info)
}

func put(c echo.Context) error {
	var info PlaceInfo

	if err := (&echo.DefaultBinder{}).BindBody(c, &info); err != nil {
		return c.String(http.StatusBadRequest, "failed to parse place info")
	}

	userId := c.Get(UserIdCtxName).(uuid.UUID)

	id := c.Param("id")
	if id != "" {
		placeId, err := placeFromString(id, key)
		if err != nil {
			return c.String(http.StatusBadRequest, "invalid place")
		}

		if placeId.UserId != userId {
			return c.String(http.StatusForbidden, "you can only change your places")
		}

		info.Long = placeId.Long
		info.Lat = placeId.Lat
	}

	id, err := PlaceId{UserId: userId, Long: info.Long, Lat: info.Lat}.toString(key)
	if err != nil {
		return err
	}

	db.Clauses(clause.OnConflict{UpdateAll: true}).Create(&PlaceData{
		Id:      id,
		Public:  info.Public,
		Secret:  info.Secret,
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

	linq.From(route).ZipT(linq.From(saved), func(placeId PlaceId, data PlaceData) PlaceInfo {
		return toPlaceInfo(userId, placeId, data)
	}).ForEachT(func(item PlaceInfo) {
		enc.Encode(item)
	})

	return nil
}

func toPlaceInfo(userId uuid.UUID, placeId PlaceId, data PlaceData) PlaceInfo {
	return PlaceInfo{
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

func login(c echo.Context) error {
	userId := uuid.New()
	signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.RegisteredClaims{Subject: userId.String()}).SignedString(JwtSecret)
	if err != nil {
		return err
	}

	cookie := new(http.Cookie)
	cookie.Name = AuthCookieName
	cookie.Value = signed
	cookie.Expires = time.Now().Add(48 * time.Hour)
	cookie.HttpOnly = true
	cookie.SameSite = http.SameSiteStrictMode
	c.SetCookie(cookie)

	return c.JSON(http.StatusOK, "signed in")
}

type PlaceInfo struct {
	Long   float64
	Lat    float64
	Public string
	Secret string
}
