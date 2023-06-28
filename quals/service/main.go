package main

import (
	"crypto/rsa"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"strconv"
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
	usersTTL        = 3600
	registerDelay   = 700 * time.Millisecond
	loginDelay      = 300 * time.Millisecond
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
	Timestamp string `json:"timestamp"`
	User      string `json:"user"`
}

var (
	users map[string]Register
	mu    sync.Mutex

	key *rsa.PrivateKey
)

func getSignedCookieData(c *gin.Context) (map[string]string, error) {
	cookieStr, err := c.Cookie(cookieName)
	if err != nil || len(cookieStr) == 0 {
		return nil, nil
	}

	signatureStr, err := c.Cookie(cookieSigName)
	if err != nil || len(signatureStr) == 0 {
		return nil, errors.New("signature not found")
	}

	ok, err := verify(cookieStr, signatureStr, &key.PublicKey)
	if err != nil {
		return nil, fmt.Errorf("verify: %w", err)
	}
	if !ok {
		return nil, fmt.Errorf("signature mismatch")
	}

	var result map[string]string
	if err := json.Unmarshal([]byte(cookieStr), &result); err != nil {
		return nil, fmt.Errorf("unmarshal: %w", err)
	}

	if timestamp, err := strconv.Atoi(result["timestamp"]); err != nil {
		return nil, fmt.Errorf("bad timestamp: %w", err)
	} else if time.Since(time.Unix(int64(timestamp), 0)) > cookieTTL*time.Second {
		return nil, fmt.Errorf("session expired")
	}

	return result, nil
}

func doRegister(form Register) error {
	time.Sleep(registerDelay)

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
	time.Sleep(loginDelay)

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

func removeOldUsers() {
	start := time.Now()

	mu.Lock()
	defer mu.Unlock()

	removed := 0
	for u := range users {
		if time.Now().Unix()-users[u].Timestamp > usersTTL {
			fmt.Printf("Removing user %q as too old\n", u)
			delete(users, u)
			removed++
		}
	}

	fmt.Printf("Removed %d users by TTL in %s\n", removed, time.Since(start))
}

func usersDBLoop() {
	for {
		time.Sleep(usersSavePeriod)

		if err := saveUsers(); err != nil {
			fmt.Printf("Error saving users: %s\n", err)
		}

		removeOldUsers()
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

func handleUser(c *gin.Context) {
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
			Timestamp: strconv.FormatInt(time.Now().Unix(), 10),
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

	// No POST form data - try to show user info (if user is logged in).

	cookie, err := getSignedCookieData(c)
	if err != nil {
		c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
		return
	}
	if cookie == nil {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	mu.Lock()
	defer mu.Unlock()

	user, ok := users[cookie["user"]]
	if !ok {
		c.HTML(http.StatusOK, template, gin.H{"Error": "user '" + cookie["user"] + "' not found"})
		return
	}

	c.HTML(http.StatusOK, template, gin.H{"User": user})
}

func handleLogout(c *gin.Context) {
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

	go usersDBLoop()

	// Set up http server

	router := gin.Default()

	router.LoadHTMLFiles(template)

	router.GET("/", handleUser)
	router.POST("/", handleUser)
	router.POST("/logout", handleLogout)

	router.Run(listen)
}
