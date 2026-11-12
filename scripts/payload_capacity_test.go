package main

import (
	"bytes"
	"encoding/base64"
	"github.com/deroproject/derohe/rpc"
	"github.com/deroproject/derohe/transaction"
	"testing"
)

func TestMessengerRelease153Boundary(t *testing.T) {
	if transaction.PAYLOAD0_LIMIT != 111 {
		t.Fatalf("unexpected argument limit: %d", transaction.PAYLOAD0_LIMIT)
	}
	for _, n := range []int{78, 79} {
		raw := make([]byte, n)
		for i := range raw {
			raw[i] = byte(i)
		}
		args := rpc.Arguments{{Name: "m", DataType: rpc.DataString, Value: base64.StdEncoding.EncodeToString(raw)}}
		encoded, err := args.MarshalBinary()
		if err != nil {
			t.Fatal(err)
		}
		expected := 110
		if n == 79 {
			expected = 114
		}
		if len(encoded) != expected {
			t.Fatalf("raw %d: encoded %d", n, len(encoded))
		}
		packed, err := args.CheckPack(transaction.PAYLOAD0_LIMIT)
		if n == 79 {
			if err == nil {
				t.Fatal("oversize accepted")
			}
			continue
		}
		if err != nil {
			t.Fatal(err)
		}
		var recovered rpc.Arguments
		if err = recovered.UnmarshalBinary(packed); err != nil {
			t.Fatal(err)
		}
		decoded, err := base64.StdEncoding.DecodeString(recovered.Value("m", rpc.DataString).(string))
		if err != nil || !bytes.Equal(raw, decoded) {
			t.Fatal("binary roundtrip mismatch")
		}
	}
	for _, n := range []int{105, 106} {
		args := rpc.Arguments{{Name: "m", DataType: rpc.DataString, Value: string(bytes.Repeat([]byte{'A'}, n))}}
		_, err := args.CheckPack(transaction.PAYLOAD0_LIMIT)
		if (n == 105 && err != nil) || (n == 106 && err == nil) {
			t.Fatalf("ASCII boundary %d: %v", n, err)
		}
	}
}
