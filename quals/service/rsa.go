package main

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"fmt"
	"os"
	"time"
)

const (
	keySize            = 768
	privateKeyFileName = "private.pem"
)

func generateKeyPair() {
	_, err := os.Stat(privateKeyFileName)
	if err == nil {
		fmt.Printf("Key file %q already exists, skip generation\n", privateKeyFileName)
		return
	}

	if err != nil && !os.IsNotExist(err) {
		panic(err)
	}

	start := time.Now()

	key, err := rsa.GenerateKey(rand.Reader, keySize)
	if err != nil {
		panic(err)
	}

	bytes := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(key),
	})

	err = os.WriteFile(privateKeyFileName, bytes, 0600)
	if err != nil {
		panic(err)
	}

	fmt.Printf("RSA key pair generated in %s\n", time.Since(start))
}

func loadPrivateKey() *rsa.PrivateKey {
	start := time.Now()

	bytes, err := os.ReadFile(privateKeyFileName)
	if err != nil {
		panic(err)
	}

	block, _ := pem.Decode(bytes)
	if block == nil {
		panic(err)
	}

	key, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		panic(err)
	}

	fmt.Printf("RSA private key loaded in %s\n", time.Since(start))
	return key
}

func sign(msg string, key *rsa.PrivateKey) (string, error) {
	start := time.Now()

	bytes := []byte(msg)
	hashed := sha256.Sum256(bytes)

	signature, err := rsa.SignPKCS1v15(rand.Reader, key, crypto.SHA256, hashed[:])
	if err != nil {
		return "", fmt.Errorf("sign: %w", err)
	}

	signature64 := base64.StdEncoding.EncodeToString(signature)
	fmt.Printf("Message (%d bytes) signed in %s (signature size %d bytes)\n",
		len(bytes), time.Since(start), len(signature))

	return signature64, nil
}

func verify(msg string, signature64 string, key *rsa.PublicKey) (bool, error) {
	start := time.Now()

	signature, err := base64.StdEncoding.DecodeString(signature64)
	if err != nil {
		return false, fmt.Errorf("base64 decode:%w", err)
	}

	bytes := []byte(msg)
	hashed := sha256.Sum256(bytes)

	ok := rsa.VerifyPKCS1v15(key, crypto.SHA256, hashed[:], signature) == nil
	fmt.Printf("Message (%d bytes) verified in %s\n", len(bytes), time.Since(start))
	return ok, nil
}
