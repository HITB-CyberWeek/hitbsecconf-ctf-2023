package main

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

const (
	listen     = ":80"
	cookieName = "ctf"
	template   = "index.tpl"
)

var (
	db *gorm.DB
)

func cookieDomain(c *gin.Context) string {
	host := strings.Split(c.Request.Host, ":")[0]
	if host == "localhost" {
		return ""
	}
	return host
}

func handleGet(c *gin.Context) {
	var count int64
	db.Model(&Record{}).Count(&count)
	c.HTML(http.StatusOK, template, gin.H{
		"Info": fmt.Sprintf("There are %d records in the database.", count),
	})
}

func handleLogin(c *gin.Context) {
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
	result := db.Where("user = ? AND pass = ?", user, password).Find(&record)

	if result.Error != nil {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": result.Error,
		})
		return
	}
	if result.RowsAffected == 0 {
		c.HTML(http.StatusOK, template, gin.H{
			"Error": "User not found",
		})
		return
	}

	c.HTML(http.StatusOK, template, gin.H{
		"Info": fmt.Sprintf("Welcome, user %s [%d]!", record.User, record.ID),
	})
	return
}

func handleRegister(c *gin.Context) {
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

	db.Create(&Record{
		User: user,
		Pass: password,
	})

	c.HTML(http.StatusOK, template, gin.H{
		"Info": "You have successfully registered!",
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

func handleLogout(c *gin.Context) {
	c.SetCookie(cookieName, "", 0, "/", cookieDomain(c), false, true)
	c.Redirect(http.StatusFound, "/")
}

func main() {

	// Open db connection

	var err error
	if db, err = Connect(); err != nil {
		panic(err)
	}

	// Set up http server

	router := gin.Default()

	router.LoadHTMLFiles(template)

	router.GET("/", handleGet)
	router.POST("/", handlePost)
	router.POST("/logout", handleLogout)

	router.Run(listen)
}
