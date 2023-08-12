package main

import "time"

type PlaceData struct {
	Id      string `gorm:"primarykey;size:64"`
	Public  string
	Secret  string
	Updated time.Time
}
