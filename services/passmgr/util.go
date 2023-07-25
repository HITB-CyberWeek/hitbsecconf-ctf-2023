package main

import (
	"fmt"
	"math/rand"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

var charset = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

func randomString(length int) string {
	b := make([]rune, length)
	for i := range b {
		b[i] = charset[rand.Intn(len(charset))]
	}
	return string(b)
}

func cookieDomain(c *gin.Context) string {
	host := strings.Split(c.Request.Host, ":")[0]
	if host == "localhost" {
		return ""
	}
	return host
}

func mustGetEnv(key string) string {
	value := os.Getenv(key)
	if value == "" {
		panic(fmt.Sprintf("environment variable %q must be set", key))
	}
	return value
}
