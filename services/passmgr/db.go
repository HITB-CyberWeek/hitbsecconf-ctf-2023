package main

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

type Record struct {
	ID        uint `gorm:"primarykey"`
	CreatedAt time.Time
	UpdatedAt time.Time

	User    string `gorm:"size:64;index"`
	Pass    string `gorm:"size:64"`
	Site    string `gorm:"size:64"`
	UserRef string `gorm:"size:64;index"`
}

type Session struct {
	ID        uint      `gorm:"primarykey"`
	CreatedAt time.Time `gorm:"index"`
	UpdatedAt time.Time

	Cookie string `gorm:"size:64;index"`
	User   string `gorm:"size:64"`
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

	verboseLogger := logger.New(
		log.New(os.Stdout, "\r\n", log.LstdFlags), // io writer
		logger.Config{
			SlowThreshold:             time.Second, // Slow SQL threshold
			LogLevel:                  logger.Info, // Log level
			IgnoreRecordNotFoundError: false,       // Ignore ErrRecordNotFound error for logger
			ParameterizedQueries:      false,       // Don't include params in the SQL log
			Colorful:                  true,        // Disable color
		},
	)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: verboseLogger,
	})
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}

	err = AutoMigrate(db)
	if err != nil {
		return nil, fmt.Errorf("auto migrate: %w", err)
	}

	return db, nil
}

func AutoMigrate(db *gorm.DB) error {
	// https://gorm.io/docs/migration.html
	// AutoMigrate will create tables, missing foreign keys, constraints,
	// columns and indexes. It will change existing column’s type if its size,
	// precision, nullable changed. It WON’T delete unused columns to protect your data.
	return db.AutoMigrate(&Record{}, &Session{})
}
