package main

import (
	"fmt"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"os"
	"strconv"
)

func mustGetEnv(key string) string {
	value := os.Getenv(key)
	if value == "" {
		panic(fmt.Sprintf("environment variable %q must be set", key))
	}
	return value
}

func MakeConnectionString() (string, error) {
	dbHost := mustGetEnv("DB_HOST")
	dbPort, err := strconv.Atoi(mustGetEnv("DB_PORT"))
	if err != nil {
		return "", fmt.Errorf("invalid port: %w", err)
	}
	dbUser := mustGetEnv("DB_USER")
	dbName := mustGetEnv("DB_NAME")
	dbPass := mustGetEnv("DB_PASS")

	conn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s target_session_attrs=read-write",
		dbHost, dbPort, dbUser, dbPass, dbName)

	return conn, nil
}

func Connect() (*gorm.DB, error) {
	dsn, err := MakeConnectionString()
	if err != nil {
		return nil, fmt.Errorf("make connection string: %w", err)
	}

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}

	err = AutoMigrate(db)
	if err != nil {
		return nil, fmt.Errorf("auto migrate: %w", err)
	}

	return db, nil
}

type Record struct {
	gorm.Model
	User    string
	Pass    string
	Site    string
	UserRef string
}

func AutoMigrate(db *gorm.DB) error {
	// https://gorm.io/docs/migration.html
	// AutoMigrate will create tables, missing foreign keys, constraints,
	// columns and indexes. It will change existing column’s type if its size,
	// precision, nullable changed. It WON’T delete unused columns to protect your data.
	return db.AutoMigrate(&Record{})
}
