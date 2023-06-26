package main

import (
	"crypto/rsa"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	listen          = ":8080"
	cookieName      = "ctf"
	cookieSigName   = "ctf.sig"
	cookieTTL       = 600
	cookieDomain    = "165.227.163.15" // FIXME
	template        = "index.tpl"
	usersFile       = "users.json"
	usersSavePeriod = 10 * time.Second
)

type Register struct {
	User      string `json:"user" form:"user" binding:"required"`
	Password  string `json:"password" form:"password" binding:"required"`
	Flag      string `json:"flag" form:"flag" binding:"required"`
	Timestamp int64  `json:"timestamp"`
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
	mu    sync.Mutex

	key *rsa.PrivateKey
)

func index(c *gin.Context) {
	cookieStr, err := c.Cookie(cookieName)
	if err != nil || len(cookieStr) == 0 {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	signatureStr, err := c.Cookie(cookieSigName)
	if err != nil || len(signatureStr) == 0 {
		c.HTML(http.StatusOK, template, gin.H{"Error": "signature cookie not found"})
		return
	}

	ok, err := verify(cookieStr, signatureStr, &key.PublicKey)
	if err != nil {
		c.HTML(http.StatusOK, template, gin.H{"Error": "signature verify: " + err.Error()})
		return
	}
	if !ok {
		c.HTML(http.StatusOK, template, gin.H{"Error": "signature mismatch"})
		return
	}

	var cookie Cookie
	if err := json.Unmarshal([]byte(cookieStr), &cookie); err != nil {
		c.HTML(http.StatusOK, template, gin.H{"Error": "json unmarshal: " + err.Error()})
		return
	}

	if time.Since(time.Unix(cookie.Timestamp, 0)) > cookieTTL*time.Second {
		c.HTML(http.StatusOK, template, gin.H{"Error": "cookie expired"})
		return
	}

	mu.Lock()
	defer mu.Unlock()

	user, ok := users[cookie.User]
	if !ok {
		c.HTML(http.StatusOK, template, gin.H{"Error": "user '" + cookie.User + "' not found"})
		return
	}

	c.HTML(http.StatusOK, template, gin.H{"User": user})
}

func doRegister(form Register) error {
	mu.Lock()
	defer mu.Unlock()

	_, ok := users[form.User]
	if ok {
		return errors.New("user already exists")
	}

	form.Timestamp = time.Now().Unix()
	users[form.User] = form

	fmt.Printf("New user registered: %+v\n", form)
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

	fmt.Printf("User logged in: %+v\n", user)
	return nil
}

func saveUsers() error {
	newUsersFile := usersFile + ".new"
	f, err := os.Create(newUsersFile)
	if err != nil {
		return fmt.Errorf("create file: %w", err)
	}
	defer f.Close()

	start := time.Now()
	mu.Lock()

	bytes, err := json.Marshal(users)
	count := len(users)

	mu.Unlock()
	lockDuration := time.Since(start)

	if err != nil {
		return fmt.Errorf("json marshal: %w", err)
	}

	f.Write(bytes)
	f.Close()

	if err := os.Rename(newUsersFile, usersFile); err != nil {
		return fmt.Errorf("rename file: %w", err)
	}

	fmt.Printf("%d users (%d bytes) have been saved to %q with %s lock\n",
		count, len(bytes), usersFile, lockDuration)
	return nil
}

func saveUsersLoop() {
	for {
		time.Sleep(usersSavePeriod)
		if err := saveUsers(); err != nil {
			fmt.Printf("Error saving users: %s\n", err)
		}
	}
}

func loadUsers() error {
	bytes, err := os.ReadFile(usersFile)
	if err != nil {
		return fmt.Errorf("read file: %w", err)
	}

	mu.Lock()
	defer mu.Unlock()

	if err := json.Unmarshal(bytes, &users); err != nil {
		return fmt.Errorf("json unmarshal: %w", err)
	}

	fmt.Printf("%d users have been loaded from %q\n", len(users), usersFile)
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
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		if err := doRegister(form); err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		c.HTML(http.StatusOK, template, gin.H{"Info": "User registered"})
		return
	}

	if len(c.PostForm("login")) > 0 {
		var form Login
		if err := c.ShouldBind(&form); err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		if err := doLogin(form); err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		cookie := Cookie{
			Timestamp: time.Now().Unix(),
			User:      form.User,
		}
		cookieStr, signatureStr, err := signCookie(cookie)
		if err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		c.SetCookie(cookieName, cookieStr, cookieTTL, "/", cookieDomain, false, true)
		c.SetCookie(cookieSigName, signatureStr, cookieTTL, "/", cookieDomain, false, true)
		c.Redirect(http.StatusFound, "/")
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

	// Set up RSA keys

	generateKeyPair()
	key = loadPrivateKey()

	// Set up users database

	users = make(map[string]Register)

	if err := loadUsers(); err != nil {
		fmt.Printf("Error loading users from file: %w\n", err)
	}

	go saveUsersLoop()

	// Set up http server

	router := gin.Default()

	router.LoadHTMLFiles(template)

	router.GET("/", index)
	router.POST("/", userPost)
	router.POST("/logout", logout)

	router.Run(listen)
}
