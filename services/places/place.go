package main

import (
	"encoding/binary"
	"encoding/hex"
	"errors"
	"github.com/google/uuid"
	"math"
)

type PlaceId struct {
	UserId uuid.UUID
	Long   float64
	Lat    float64
}

func (placeId PlaceId) putBytes(dst []byte) error {
	if len(dst) < 32 {
		return errors.New("place: failed to serialize")
	}

	copy(dst, placeId.UserId[:])
	binary.LittleEndian.PutUint64(dst[16:], math.Float64bits(placeId.Long))
	binary.LittleEndian.PutUint64(dst[24:], math.Float64bits(placeId.Lat))

	return nil
}

func placeFromBytes(src []byte) (PlaceId, error) {
	if src == nil || len(src) != 32 {
		return PlaceId{}, errors.New("place: failed to parse")
	}

	userId, err := uuid.FromBytes(src[0:16])
	if err != nil {
		return PlaceId{}, err
	}

	long := math.Float64frombits(binary.LittleEndian.Uint64(src[16:]))
	lat := math.Float64frombits(binary.LittleEndian.Uint64(src[24:]))

	return PlaceId{UserId: userId, Long: long, Lat: lat}, nil
}

func (placeId PlaceId) toString(key []byte) (string, error) {
	data := make([]byte, 32)

	err := placeId.putBytes(data)
	if err != nil {
		return "", nil
	}

	err = encrypt(data, key)
	if err != nil {
		return "", nil
	}

	return hex.EncodeToString(data), nil
}

func placeFromString(value string, key []byte) (PlaceId, error) {
	data, err := hex.DecodeString(value)
	if err != nil {
		return PlaceId{}, err
	}

	err = decrypt(data, key)
	if err != nil {
		return PlaceId{}, err
	}

	placeId, err := placeFromBytes(data)
	if err != nil {
		return PlaceId{}, err
	}

	return placeId, nil
}
