// shipping-svc — trivial Java HTTP service. Fixture only, not organization-specific.
package shipping;

import org.springframework.web.bind.annotation.*;

@RestController
public class Shipping {

    @GetMapping("/shipments/{id}")
    public Shipment getShipment(@PathVariable String id) {
        // BHV: returns shipment tracking status for a given shipment id
        return new Shipment(id, "IN_TRANSIT");
    }

    record Shipment(String id, String status) {}
}
