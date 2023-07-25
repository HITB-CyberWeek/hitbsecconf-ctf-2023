// Modes for index.go.html

package main

type User struct {
	Name string
}

type Stats struct {
	Users    int64
	Sessions int64
}

type Site struct {
	Address string
	User    string
	Pass    string
}
