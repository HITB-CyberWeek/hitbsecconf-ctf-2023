package main

import (
	"crypto/aes"
	"crypto/cipher"
	"errors"
)

const BlockSize = 16

func crypt(data, key []byte, crypt func(cipher cipher.Block, data []byte)) error {
	if len(key) != BlockSize || (len(data)&(BlockSize-1)) != 0 {
		return errors.New("crypt: data to encrypt/decrypt must be a multiple of block size")
	}

	block, err := aes.NewCipher([]byte(key))
	if err != nil {
		return err
	}

	for idx := 0; idx < len(data); idx += BlockSize {
		end := idx + BlockSize
		crypt(block, data[idx:end])
	}

	return nil
}

func Encrypt(data, key []byte) error {
	return crypt(data, key, func(cipher cipher.Block, data []byte) {
		cipher.Encrypt(data, data)
	})
}

func Decrypt(data, key []byte) error {
	return crypt(data, key, func(cipher cipher.Block, data []byte) {
		cipher.Decrypt(data, data)
	})
}
