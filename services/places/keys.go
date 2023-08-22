package main

import (
	"crypto/rand"
	"os"
	"path/filepath"
)

func LoadOrCreateKey(file string, size int32) []byte {
	bytes, err := os.ReadFile(file)
	if err == nil {
		return bytes
	}

	if !os.IsNotExist(err) {
		panic(err)
	}

	err = os.Mkdir(filepath.Dir(file), 0750)
	if err != nil && !os.IsExist(err) {
		panic(err)
	}

	bytes = make([]byte, size)
	_, err = rand.Read(bytes)
	if err != nil {
		panic(err)
	}

	err = os.WriteFile(file, bytes, 0640)
	if err != nil {
		panic(err)
	}

	return bytes
}
