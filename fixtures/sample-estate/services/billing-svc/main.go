// billing-svc — trivial Go HTTP service. Fixture only, not organization-specific.
package main

import (
	"encoding/json"
	"net/http"
)

// invoice.status lifecycle: OPEN -> CLOSED (invoice lifecycle, not order lifecycle)
type Invoice struct {
	ID     string `json:"id"`
	Status string `json:"status"`
}

func createInvoice(w http.ResponseWriter, r *http.Request) {
	inv := Invoice{ID: "inv-1", Status: "OPEN"}
	json.NewEncoder(w).Encode(inv)
}

// consumeOrderCreated handles the "order.created" topic, consumer group "billing-svc".
func consumeOrderCreated(order map[string]interface{}) {
	// creates an invoice for the order; unrelated to Order.status
}

func main() {
	http.HandleFunc("/invoices", createInvoice)
	http.ListenAndServe(":8080", nil)
}
