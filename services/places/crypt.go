package main

import (
	"crypto/aes"
	"crypto/cipher"
	"errors"
)

const (
	size = 16
)

func crypt(data, key []byte, crypt func(cipher cipher.Block, data []byte)) error {
	if len(key) != size || (len(data)&(size-1)) != 0 {
		return errors.New("crypt: data to encrypt/decrypt must be a multiple of block size")
	}

	block, err := aes.NewCipher([]byte(key))
	if err != nil {
		return err
	}

	for idx := 0; idx < len(data); idx += size {
		end := idx + size
		crypt(block, data[idx:end])
	}

	return nil
}

func encrypt(data, key []byte) error {
	return crypt(data, key, func(cipher cipher.Block, data []byte) {
		cipher.Encrypt(data, data)
	})
}

func decrypt(data, key []byte) error {
	return crypt(data, key, func(cipher cipher.Block, data []byte) {
		cipher.Decrypt(data, data)
	})
}
