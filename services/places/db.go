package main

import "time"

type PlaceData struct {
	Id        string `gorm:"primarykey;size:64"`
	CreatedAt time.Time
	Public    string
	Secret    string
}
