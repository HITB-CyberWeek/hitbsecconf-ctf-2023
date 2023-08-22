package main

import (
	"encoding/binary"
	"encoding/hex"
	"errors"
	"github.com/google/uuid"
	"math"
)

const PlaceIdSize = 32

type PlaceId struct {
	UserId uuid.UUID
	Lat    float64
	Long   float64
}

func (placeId PlaceId) putBytes(dst []byte) error {
	if len(dst) < PlaceIdSize {
		return errors.New("placeId: failed to serialize")
	}

	copy(dst, placeId.UserId[:])
	binary.LittleEndian.PutUint64(dst[16:], math.Float64bits(placeId.Lat))
	binary.LittleEndian.PutUint64(dst[24:], math.Float64bits(placeId.Long))

	return nil
}

func placeIdFromBytes(src []byte) (PlaceId, error) {
	if src == nil || len(src) != PlaceIdSize {
		return PlaceId{}, errors.New("placeId: failed to parse")
	}

	userId, err := uuid.FromBytes(src[0:16])
	if err != nil {
		return PlaceId{}, err
	}

	lat := math.Float64frombits(binary.LittleEndian.Uint64(src[16:]))
	long := math.Float64frombits(binary.LittleEndian.Uint64(src[24:]))

	return PlaceId{UserId: userId, Lat: lat, Long: long}, nil
}

func (placeId PlaceId) ToString(key []byte) (string, error) {
	data := make([]byte, PlaceIdSize)

	err := placeId.putBytes(data)
	if err != nil {
		return "", err
	}

	err = Encrypt(data, key)
	if err != nil {
		return "", err
	}

	return hex.EncodeToString(data), nil
}

func PlaceIdFromString(value string, key []byte) (PlaceId, error) {
	data, err := hex.DecodeString(value)
	if err != nil {
		return PlaceId{}, err
	}

	err = Decrypt(data, key)
	if err != nil {
		return PlaceId{}, err
	}

	placeId, err := placeIdFromBytes(data)
	if err != nil {
		return PlaceId{}, err
	}

	return placeId, nil
}
