// Run inside the exact official DERO source checkout under investigation.
package main

import (
 "bytes"
 "encoding/base64"
 "fmt"
 "github.com/deroproject/derohe/config"
 "github.com/deroproject/derohe/rpc"
 "github.com/deroproject/derohe/transaction"
)

func main() {
 fmt.Printf("version=%s argument_limit=%d\n", config.Version, transaction.PAYLOAD0_LIMIT)
 for _, n := range []int{24, 78, 79, 102, 103} {
  raw := make([]byte, n)
  for i := range raw { raw[i] = byte(i) }
  args := rpc.Arguments{{Name:"m", DataType:rpc.DataString, Value:base64.StdEncoding.EncodeToString(raw)}}
  encoded, err := args.MarshalBinary()
  packed, packErr := args.CheckPack(transaction.PAYLOAD0_LIMIT)
  equal := false
  if packErr == nil {
   var decoded rpc.Arguments
   if err := decoded.UnmarshalBinary(packed); err != nil { panic(err) }
   value := decoded.Value("m", rpc.DataString).(string)
   recovered, err := base64.StdEncoding.DecodeString(value)
   equal = err == nil && bytes.Equal(raw, recovered)
  }
  fmt.Printf("raw=%d CBOR=%d marshal=%v pack=%v roundtrip=%v\n",n,len(encoded),err,packErr,equal)
 }
}
