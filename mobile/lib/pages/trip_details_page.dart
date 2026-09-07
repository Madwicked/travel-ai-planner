import 'package:flutter/material.dart';

import 'hotel_options_page.dart';
import 'itinerary_page.dart';
import 'place_options_page.dart';
import 'transport_options_page.dart';
import '../models/hotel.dart';
import '../models/place.dart';
import '../models/transport.dart';
import '../services/hotel_service.dart';
import '../services/place_service.dart';
import '../services/transport_service.dart';

class TripDetailsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const TripDetailsPage({super.key, required this.trip});

  @override
  State<TripDetailsPage> createState() => _TripDetailsPageState();
}

class _TripDetailsPageState extends State<TripDetailsPage> {
  Transport? selectedOutboundTransport;
  Transport? selectedReturnTransport;

  Hotel? selectedHotel;

  List<Place> selectedPlaces = [];

  bool isLoadingTransport = true;
  bool isLoadingHotel = true;
  bool isLoadingPlaces = true;

  @override
  void initState() {
    super.initState();

    loadSelectedTransports();
    loadSelectedHotel();
    loadSelectedPlaces();
  }

  // =========================
  // TRANSPORT
  // =========================

  Future<void> loadSelectedTransports() async {
    final tripId = widget.trip['id'];

    try {
      final transports = await TransportService.getTransports(tripId);

      if (!mounted) return;

      setState(() {
        for (final transport in transports) {
          if (transport.direction == 'outbound') {
            selectedOutboundTransport = transport;
          }

          if (transport.direction == 'return') {
            selectedReturnTransport = transport;
          }
        }

        isLoadingTransport = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingTransport = false;
      });
    }
  }

  Future<void> saveTransport(Transport transport) async {
    final tripId = widget.trip['id'];

    try {
      await TransportService.createTransport(
        tripId: tripId,
        transport: transport,
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to save transport: $e')));
    }
  }

  Future<void> chooseOutboundTransport() async {
    final trip = {...widget.trip, 'return_transport': false};

    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => TransportOptionsPage(trip: trip)),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport = result as Transport;

    await saveTransport(transport);

    if (!context.mounted) return;

    setState(() {
      selectedOutboundTransport = transport;
    });
  }

  Future<void> chooseReturnTransport() async {
    final trip = {...widget.trip, 'return_transport': true};

    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => TransportOptionsPage(trip: trip)),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport = result as Transport;

    await saveTransport(transport);

    if (!context.mounted) return;

    setState(() {
      selectedReturnTransport = transport;
    });
  }

  // =========================
  // HOTEL
  // =========================

  Future<void> loadSelectedHotel() async {
    final tripId = widget.trip['id'];

    try {
      final hotels = await HotelService.getHotels(tripId);

      if (!mounted) return;

      setState(() {
        if (hotels.isNotEmpty) {
          selectedHotel = hotels.last;
        }

        isLoadingHotel = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingHotel = false;
      });
    }
  }

  Future<void> chooseHotel() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => HotelOptionsPage(trip: widget.trip),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final hotel = result as Hotel;

    final tripId = widget.trip['id'];

    try {
      final savedHotel = await HotelService.createHotel(
        tripId: tripId,
        hotel: hotel,
      );

      if (!context.mounted) return;

      setState(() {
        selectedHotel = savedHotel;
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Hotel saved')));
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to save hotel: $e')));
    }
  }

  // =========================
  // PLACES
  // =========================

  Future<void> loadSelectedPlaces() async {
    final tripId = widget.trip['id'];

    try {
      final places = await PlaceService.getPlaces(tripId);

      if (!mounted) return;

      setState(() {
        selectedPlaces = places;
        isLoadingPlaces = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingPlaces = false;
      });
    }
  }

  Future<void> choosePlaces() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlaceOptionsPage(trip: widget.trip),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final places = List<Place>.from(result);

    final tripId = widget.trip['id'];

    try {
      final savedPlaces = <Place>[];

      for (final place in places) {
        final savedPlace = await PlaceService.createPlace(
          tripId: tripId,
          place: place,
        );

        savedPlaces.add(savedPlace);
      }

      if (!context.mounted) return;

      setState(() {
        selectedPlaces = savedPlaces;
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Places saved')));
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to save places: $e')));
    }
  }

  // =========================
  // TRANSPORT CARD
  // =========================

  Widget buildTransportCard(
    Transport transport, {
    required VoidCallback onChange,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${transport.departureLocation} → '
              '${transport.arrivalLocation}',
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 6),

            Text('${transport.departureDate}'),

            const SizedBox(height: 4),

            Text(
              '${transport.departureTime} → '
              '${transport.arrivalTime}',
            ),

            const SizedBox(height: 8),

            Text(
              '€${transport.price}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: onChange,
                child: const Text('Change transport'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // =========================
  // PLACE CARD
  // =========================

  Widget buildPlaceCard(Place place) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              place.name,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 6),

            Text(place.city),

            const SizedBox(height: 4),

            Text(place.address, style: TextStyle(color: Colors.grey.shade600)),
          ],
        ),
      ),
    );
  }

  // =========================
  // BUILD
  // =========================

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Trip Details',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              destination,
              style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            Text(
              '${widget.trip['start_date']} → '
              '${widget.trip['end_date']}',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 28),

            // =========================
            // OUTBOUND TRANSPORT
            // =========================
            const Text(
              'Outbound Transport',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            if (isLoadingTransport)
              const Center(child: CircularProgressIndicator())
            else if (selectedOutboundTransport != null)
              buildTransportCard(
                selectedOutboundTransport!,
                onChange: chooseOutboundTransport,
              )
            else
              ElevatedButton(
                onPressed: chooseOutboundTransport,
                child: const Text('Choose outbound transport'),
              ),

            const SizedBox(height: 24),

            // =========================
            // RETURN TRANSPORT
            // =========================
            const Text(
              'Return Transport',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            if (isLoadingTransport)
              const Center(child: CircularProgressIndicator())
            else if (selectedReturnTransport != null)
              buildTransportCard(
                selectedReturnTransport!,
                onChange: chooseReturnTransport,
              )
            else
              ElevatedButton(
                onPressed: chooseReturnTransport,
                child: const Text('Choose return transport'),
              ),

            const SizedBox(height: 24),

            // =========================
            // HOTEL
            // =========================
            const Text(
              'Hotel',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            if (isLoadingHotel)
              const Center(child: CircularProgressIndicator())
            else if (selectedHotel != null)
              Card(
                margin: const EdgeInsets.only(bottom: 12),
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.hotel,
                          color: Colors.blue,
                          size: 28,
                        ),
                      ),

                      const SizedBox(width: 16),

                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              selectedHotel!.name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 6),

                            Text(
                              selectedHotel!.city,
                              style: const TextStyle(fontSize: 15),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              selectedHotel!.address,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey.shade600,
                              ),
                            ),

                            const SizedBox(height: 10),

                            Text(
                              '${selectedHotel!.checkIn.day.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkIn.month.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkIn.year} → '
                              '${selectedHotel!.checkOut.day.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkOut.month.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkOut.year}',
                              style: const TextStyle(fontSize: 15),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              '${selectedHotel!.nights} '
                              '${selectedHotel!.nights == 1 ? 'night' : 'nights'}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(width: 8),

                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '€${selectedHotel!.totalPrice}',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),

                          const SizedBox(height: 4),

                          Text(
                            '€${selectedHotel!.pricePerNight}/night',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              )
            else
              ElevatedButton(
                onPressed: chooseHotel,
                child: const Text('Choose hotel'),
              ),

            const SizedBox(height: 24),

            // =========================
            // PLACES
            // =========================
            const Text(
              'Places',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 12),

            if (isLoadingPlaces)
              const Center(child: CircularProgressIndicator())
            else if (selectedPlaces.isNotEmpty)
              ...selectedPlaces.map(buildPlaceCard)
            else
              ElevatedButton(
                onPressed: choosePlaces,
                child: const Text('Choose places'),
              ),

            const SizedBox(height: 24),

            // =========================
            // ITINERARY
            // =========================
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ItineraryPage(trip: widget.trip),
                    ),
                  );
                },
                child: const Text('View itinerary'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
