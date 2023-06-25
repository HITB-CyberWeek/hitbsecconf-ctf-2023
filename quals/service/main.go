package main

import (
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
)

type UserData struct {
	Pass    string
	Address string
}

var (
	db map[string]UserData
	mu sync.Mutex
)

func userGet(c *gin.Context) {
	name := c.Param("name")

	c.String(http.StatusOK, "Hello, "+name+"!")
}

func userPost(c *gin.Context) {
	user := c.PostForm("user")
	pass := c.PostForm("pass")
	address := c.PostForm("address")

	if len(user) == 0 {
		c.String(http.StatusBadRequest, "Error: user not specified")
		return
	}

	if len(pass) == 0 {
		c.String(http.StatusBadRequest, "Error: pass not specified")
		return
	}

	if len(address) == 0 {
		c.String(http.StatusBadRequest, "Error: address not specified")
		return
	}

	mu.Lock()
	defer mu.Unlock()

	_, ok := db[user]
	if ok {
		c.String(http.StatusBadRequest, "Error: such user already exists")
		return
	}

	db[user] = UserData{
		Pass:    pass,
		Address: address,
	}
	c.String(http.StatusOK, "OK: user "+user+" registered")
}

func login(c *gin.Context) {
	user := c.PostForm("user")
	pass := c.PostForm("pass")

	if len(user) == 0 {
		c.String(http.StatusBadRequest, "Error: user not specified")
		return
	}

	if len(pass) == 0 {
		c.String(http.StatusBadRequest, "Error: pass not specified")
		return
	}

	mu.Lock()
	defer mu.Unlock()

	item, ok := db[user]
	if !ok {
		c.String(http.StatusBadRequest, "Error: no such user")
		return
	}

	if item.Pass != pass {
		c.String(http.StatusBadRequest, "Error: bad password")
		return
	}

	c.String(http.StatusOK, "OK: logged in")
}

func logout(c *gin.Context) {
}

func main() {
	db = make(map[string]UserData)

	router := gin.Default()

	router.StaticFile("/", "index.htm")

	router.GET("/user/:name", userGet)
	router.POST("/user", userPost)
	router.POST("/logout", logout)

	router.Run("localhost:8080")
}
