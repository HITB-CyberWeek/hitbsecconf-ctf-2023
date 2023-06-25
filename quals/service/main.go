package main

import (
	"crypto/rsa"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	listen        = ":8080"
	cookieName    = "ctf"
	cookieSigName = "ctf.sig"
	cookieTTL     = 600
	cookieDomain  = "165.227.163.15" // FIXME
)

type Register struct {
	User     string `form:"user" binding:"required"`
	Password string `form:"password" binding:"required"`
	Flag     string `form:"flag" binding:"required"`
}

type Login struct {
	User     string `form:"user" binding:"required"`
	Password string `form:"password" binding:"required"`
}

type Cookie struct {
	Timestamp int64  `json:"timestamp"`
	User      string `json:"user"`
}

var (
	users map[string]Register // FIXME: sync do disk
	key   *rsa.PrivateKey
	mu    sync.Mutex
)

func userGet(c *gin.Context) {
	cookieStr, err := c.Cookie(cookieName)
	if err != nil || len(cookieStr) == 0 {
		c.String(http.StatusForbidden, "Error: cookie not found")
		return
	}

	signatureStr, err := c.Cookie(cookieSigName)
	if err != nil || len(signatureStr) == 0 {
		c.String(http.StatusForbidden, "Error: signature cookie not found")
		return
	}

	ok, err := verify(cookieStr, signatureStr, &key.PublicKey)
	if err != nil {
		c.String(http.StatusInternalServerError, "Error: signature verification failed: "+err.Error())
		return
	}
	if !ok {
		c.String(http.StatusForbidden, "Error: cookie/signature mismatch")
		return
	}

	var cookie Cookie
	if err := json.Unmarshal([]byte(cookieStr), &cookie); err != nil {
		c.String(http.StatusBadRequest, "Error: json unmarshal: "+err.Error())
		return
	}

	if time.Since(time.Unix(cookie.Timestamp, 0)) > cookieTTL*time.Second {
		c.String(http.StatusForbidden, "Error: cookie expired")
		return
	}

	mu.Lock()
	defer mu.Unlock()

	user, ok := users[cookie.User]
	if !ok {
		c.String(http.StatusNotFound, fmt.Sprintf("Error: user %q not found", cookie.User))
		return
	}

	msg := fmt.Sprintf("Welcome, %s! Your flag is: %s.", cookie.User, user.Flag)
	c.String(http.StatusOK, msg)
}

func doRegister(form Register) error {
	mu.Lock()
	defer mu.Unlock()

	_, ok := users[form.User]
	if ok {
		return errors.New("user already exists")
	}

	users[form.User] = form
	return nil
}

func doLogin(form Login) error {
	mu.Lock()
	defer mu.Unlock()

	user, ok := users[form.User]
	if !ok {
		return errors.New("no such user")
	}

	if user.Password != form.Password {
		return errors.New("wrong password")
	}

	return nil
}

func signCookie(c Cookie) (string, string, error) {
	bytes, err := json.Marshal(c)
	if err != nil {
		return "", "", fmt.Errorf("json marshal: %w", err)
	}

	cookieStr := string(bytes)
	signatureStr, err := sign(cookieStr, key)
	if err != nil {
		return "", "", fmt.Errorf("sign: %w", err)
	}

	return cookieStr, signatureStr, nil
}

func userPost(c *gin.Context) {
	if len(c.PostForm("register")) > 0 {
		var form Register
		if err := c.ShouldBind(&form); err != nil {
			c.String(http.StatusBadRequest, err.Error())
			return
		}

		if err := doRegister(form); err != nil {
			c.String(http.StatusInternalServerError, err.Error())
			return
		}

		c.String(http.StatusOK, "OK: user registered")
		return
	}

	if len(c.PostForm("login")) > 0 {
		var form Login
		if err := c.ShouldBind(&form); err != nil {
			c.String(http.StatusBadRequest, err.Error())
			return
		}

		if err := doLogin(form); err != nil {
			c.String(http.StatusInternalServerError, err.Error())
			return
		}

		cookie := Cookie{
			Timestamp: time.Now().Unix(),
			User:      form.User,
		}
		cookieStr, signatureStr, err := signCookie(cookie)
		if err != nil {
			c.String(http.StatusInternalServerError, err.Error())
			return
		}

		c.SetCookie(cookieName, cookieStr, cookieTTL, "/", cookieDomain, false, true)
		c.SetCookie(cookieSigName, signatureStr, cookieTTL, "/", cookieDomain, false, true)

		c.Redirect(http.StatusFound, "/user/")
		return
	}

	c.String(http.StatusBadRequest, "Error: no action specified (login/register)")
}

func logout(c *gin.Context) {
	c.SetCookie(cookieName, "", 0, "/", cookieDomain, false, true)
	c.SetCookie(cookieSigName, "", 0, "/", cookieDomain, false, true)
	c.Redirect(http.StatusFound, "/")
}

func main() {
	users = make(map[string]Register)

	generateKeyPair()
	key = loadPrivateKey()

	router := gin.Default()

	router.StaticFile("/", "index.htm")

	router.GET("/user", userGet)
	router.POST("/user", userPost)
	router.GET("/logout", logout)

	router.Run(":8080")
}
