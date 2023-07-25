package main

import (
	"fmt"
	"math/rand"
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
	var stats Stats
	db.Model(&Record{}).Count(&stats.Users)
	db.Model(&Session{}).Count(&stats.Sessions)

	cookieValue, err := c.Cookie(cookieName)
	if err != nil || len(cookieValue) == 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Stats": stats,
		})
		return
	}

	var session Session
	result := db.Where("cookie = ?", cookieValue).Find(&session)
	if result.Error != nil || result.RowsAffected == 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Stats": stats,
		})
		return
	}

	var records []Record
	var sites []Site
	db.Where("user_ref = ?", session.User).Find(&records)
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
		"Stats": stats,
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

	cookieValue := randomString(32)
	db.Create(&Session{
		Cookie: cookieValue,
		User:   user,
	})
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
	if result.RowsAffected > 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": "User already exists",
		})
		return
	}

	db.Create(&Record{
		User: user,
		Pass: password,
	})

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

	db.Create(&Record{
		User:    user,
		Pass:    password,
		Site:    address,
		UserRef: session.User,
	})

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

	// Init random number generator

	rand.Seed(time.Now().UnixNano())

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
