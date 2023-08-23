package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

const (
	listen        = ":80"
	cookieName    = "ctf"
	template      = "index.go.html"
	sessionTTL    = 600
	registerDelay = 700 * time.Millisecond
	loginDelay    = 300 * time.Millisecond
	addDelay      = 500 * time.Millisecond
)

var (
	db *gorm.DB
)

func handleGet(c *gin.Context) {
	cookieValue, err := c.Cookie(cookieName)
	if err != nil || len(cookieValue) == 0 {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	var session Session
	result := db.Where("cookie = ?", cookieValue).Find(&session)
	if result.Error != nil || result.RowsAffected == 0 {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	var records []Record
	var sites []Site
	result = db.Where("user_ref = ?", session.User).Find(&records)
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}

	for _, r := range records {
		sites = append(sites, Site{
			Address: r.Site,
			User:    r.User,
			Pass:    r.Pass,
		})
	}

	c.HTML(http.StatusOK, template, gin.H{
		"User": User{
			Name: session.User,
		},
		"Sites": sites,
	})
}

func handleLogin(c *gin.Context) {
	time.Sleep(loginDelay)

	user := c.PostForm("user")
	if user == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("User not specified"),
		})
		return
	}

	password := c.PostForm("password")
	if password == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("Password not specified"),
		})
		return
	}

	var record Record
	result := db.Where("\"user\" = ? AND pass = ? AND user_ref = ''", user, password).Find(&record)

	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}
	if result.RowsAffected == 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": "Invalid credentials",
		})
		return
	}

	cookieValue, err := randomString(32)
	if err != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": "Session generation error",
		})
		return
	}

	result = db.Create(&Session{
		Cookie: cookieValue,
		User:   user,
	})
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}

	c.SetCookie(cookieName, cookieValue, sessionTTL, "/", cookieDomain(c), false, true)
	c.Redirect(http.StatusFound, "/")
}

func handleRegister(c *gin.Context) {
	time.Sleep(registerDelay)

	user := c.PostForm("user")
	if user == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("User not specified"),
		})
		return
	}

	password := c.PostForm("password")
	if password == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("Password not specified"),
		})
		return
	}

	var record Record
	result := db.Where("\"user\" = ? AND user_ref = ''", user).Find(&record)
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}
	if result.RowsAffected > 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": "User already exists",
		})
		return
	}

	result = db.Create(&Record{
		User: user,
		Pass: password,
	})
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}

	c.HTML(http.StatusOK, template, gin.H{
		"Info": "You have successfully registered! Now you may log in.",
	})
}

func handlePost(c *gin.Context) {
	if c.PostForm("login") != "" {
		handleLogin(c)
	} else if c.PostForm("register") != "" {
		handleRegister(c)
	} else {
		c.Redirect(http.StatusFound, "/")
	}
}

func handleAdd(c *gin.Context) {
	time.Sleep(addDelay)

	address := c.PostForm("address")
	if address == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("Address not specified"),
		})
		return
	}

	user := c.PostForm("user")
	if user == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("User not specified"),
		})
		return
	}

	password := c.PostForm("password")
	if password == "" {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": fmt.Sprintf("Password not specified"),
		})
		return
	}

	cookieValue, err := c.Cookie(cookieName)
	if err != nil || len(cookieValue) == 0 {
		c.Redirect(http.StatusFound, "/")
		return
	}

	var session Session
	result := db.Where("cookie = ?", cookieValue).Find(&session)
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	result = db.Create(&Record{
		User:    user,
		Pass:    password,
		Site:    address,
		UserRef: session.User,
	})
	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}

	c.Redirect(http.StatusFound, "/")
}

func handleLogout(c *gin.Context) {
	cookieValue, err := c.Cookie(cookieName)
	if err == nil && len(cookieValue) > 0 {
		db.Where("cookie = ?", cookieValue).Delete(&Session{})
	}

	c.SetCookie(cookieName, "", 0, "/", cookieDomain(c), false, true)
	c.Redirect(http.StatusFound, "/")
}

func sessionCleaner() {
	for {
		db.Where("created_at < ?", time.Now().Add(-time.Second*sessionTTL)).Delete(&Session{})
		time.Sleep(60 * time.Second)
	}
}

func main() {

	// Open db connection

	var err error
	if db, err = Connect(); err != nil {
		panic(err)
	}

	// Start up session cleaner

	go sessionCleaner()

	// Set up http server

	router := gin.Default()

	router.LoadHTMLFiles(template)

	router.GET("/", handleGet)
	router.POST("/", handlePost)
	router.POST("/add", handleAdd)
	router.POST("/logout", handleLogout)

	router.Run(listen)
}
