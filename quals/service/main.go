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

type DBUser struct {
	User      string `json:"user"`
	Password  string `json:"password"`
	Flag      string `json:"flag"`
	Timestamp int64  `json:"timestamp"`
}

type Cookie struct {
	User      string `json:"user"`
	Timestamp string `json:"timestamp"`
}

var (
	users map[string]DBUser // name -> DBUser
	mu    sync.Mutex

	key *rsa.PrivateKey
)

func getSignedCookieData(c *gin.Context) (map[string]string, error) {
	result := make(map[string]string)

	cookieStr, err := c.Cookie(cookieName)
	if err != nil || len(cookieStr) == 0 {
		return result, nil
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

func updatePostFormData(c *gin.Context, data map[string]string) {
	for _, f := range []string{"login", "register", "user", "password", "flag"} {
		value := c.PostForm(f)
		if len(value) > 0 {
			data[f] = value
		}
	}
}

func doRegister(data map[string]string) error {
	time.Sleep(registerDelay)

	mu.Lock()
	defer mu.Unlock()

	_, ok := users[data["user"]]
	if ok {
		return errors.New("user already exists")
	}

	u := DBUser{
		User:      data["user"],
		Password:  data["password"],
		Flag:      data["flag"],
		Timestamp: time.Now().Unix(),
	}
	if len(u.User) < 4 || len(u.User) > 20 {
		return errors.New("invalid user name")
	}
	if len(u.Password) < 4 || len(u.Password) > 20 {
		return errors.New("invalid password")
	}
	if len(u.Flag) < 4 || len(u.Flag) > 40 {
		return errors.New("invalid flag")
	}

	users[u.User] = u

	fmt.Printf("New user registered: %+v\n", u)
	return nil
}

func doLogin(data map[string]string) error {
	time.Sleep(loginDelay)

	mu.Lock()
	defer mu.Unlock()

	user, ok := users[data["user"]]
	if !ok {
		return errors.New("no such user")
	}

	if user.Password != data["password"] {
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

	data, err := getSignedCookieData(c)
	if err != nil {
		c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
		return
	}

	updatePostFormData(c, data)

	if len(data["register"]) > 0 {
		if err := doRegister(data); err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		c.HTML(http.StatusOK, template, gin.H{"Info": "User registered."})
		return
	}

	if len(data["login"]) > 0 {
		if err := doLogin(data); err != nil {
			c.HTML(http.StatusOK, template, gin.H{"Error": err.Error()})
			return
		}

		cookie := Cookie{
			Timestamp: strconv.FormatInt(time.Now().Unix(), 10),
			User:      data["user"],
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

	if len(data["user"]) == 0 {
		c.HTML(http.StatusOK, template, gin.H{})
		return
	}

	mu.Lock()
	defer mu.Unlock()

	user, ok := users[data["user"]]
	if ok {
		c.HTML(http.StatusOK, template, gin.H{"User": user})
		return
	}

	c.HTML(http.StatusOK, template, gin.H{"Error": "user '" + data["user"] + "' not found"})
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

	users = make(map[string]DBUser)

	if err := loadUsers(); err != nil {
		fmt.Printf("Error loading users from file: %s\n", err)
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
