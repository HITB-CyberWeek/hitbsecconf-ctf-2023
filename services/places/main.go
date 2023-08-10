package main

import (
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

const dbfile string = "data.db"

var key = []byte(`1234567890abcdef`)

var db *gorm.DB

func main() {
	var err error

	db, err = gorm.Open(sqlite.Open(dbfile), &gorm.Config{})
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
			SigningKey:    []byte("secret"),
			SigningMethod: jwt.SigningMethodHS256.Name,
			TokenLookup:   "cookie:auth",
			SuccessHandler: func(c echo.Context) {
				var userId uuid.UUID
				subject, err := c.Get("token").(*jwt.Token).Claims.(jwt.MapClaims).GetSubject()
				if err != nil {
					userId = uuid.UUID{}
				}
				userId, err = uuid.Parse(subject)
				if err != nil {
					userId = uuid.UUID{}
				}
				c.Set("userId", userId)
			},
			ContextKey: "token",
		}))

		r.PUT("/place", put)
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
	result := db.Limit(1).Find(&data)
	if result.Error != nil {
		return err
	}

	userId := c.Get("userId")
	info := PlaceInfo{Lat: placeId.Lat, Long: placeId.Long, Public: data.Public}
	if placeId.UserId == userId {
		info.Secret = data.Secret
	}

	return c.JSON(http.StatusOK, info)
}

func put(c echo.Context) error {
	var data PlaceInfo

	if err := (&echo.DefaultBinder{}).BindBody(c, &data); err != nil || data.Public == "" {
		return c.String(http.StatusBadRequest, "failed to parse place info")
	}

	result, err := PlaceId{
		UserId: c.Get("userId").(uuid.UUID),
		Long:   data.Long,
		Lat:    data.Lat,
	}.toString(key)
	if err != nil {
		return err
	}

	db.Clauses(clause.OnConflict{UpdateAll: true}).Create(&PlaceData{
		Id:        result,
		CreatedAt: time.Now(),
		Public:    data.Public,
		Secret:    data.Secret,
	})

	return c.String(http.StatusOK, result)
}

func route(c echo.Context) error {
	var places []string
	if err := (&echo.DefaultBinder{}).BindBody(c, &places); err != nil {
		return c.String(http.StatusBadRequest, "failed to parse route")
	}

	var route []PlaceId
	linq.From(places).
		OrderByT(func(item string) string { return item }).
		SelectT(func(item string) PlaceId {
			placeId, err := placeFromString(item, key)
			if err != nil {
				return PlaceId{}
			}
			return placeId
		}).
		WhereT(func(item PlaceId) bool {
			return item != PlaceId{}
		}).
		Distinct().
		ToSlice(&route)

	//var saved []PlaceData
	//result := db.Order("Id asc").Find(&saved, places)
	//if result.RowsAffected != int64(len(route)) {
	//	return c.String(http.StatusBadRequest, "invalid route")
	//}
	var err error
	saved := make([]PlaceData, len(route))
	linq.From(places).OrderByT(func(item string) string { return item }).SelectT(func(item string) PlaceData {
		data := PlaceData{Id: item}
		result := db.Take(&data)
		if result.Error != nil {
			err = result.Error
		}
		return data
	}).ToSlice(&saved)
	if err != nil {
		return c.String(http.StatusBadRequest, "invalid route")
	}

	var response []PlaceInfo
	linq.From(route).ZipT(linq.From(saved), func(id PlaceId, data PlaceData) PlaceInfo {
		secret := ""
		if id.UserId == c.Get("userId") {
			secret = data.Secret
		}
		return PlaceInfo{
			Long:   id.Long,
			Lat:    id.Lat,
			Public: data.Public,
			Secret: secret,
		}
	}).ToSlice(&response)

	return c.JSON(http.StatusOK, response)
}

func login(c echo.Context) error {
	userId := uuid.New()
	signed, err := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.RegisteredClaims{Subject: userId.String()}).SignedString([]byte("secret"))
	if err != nil {
		return err
	}

	cookie := new(http.Cookie)
	cookie.Name = "auth"
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
