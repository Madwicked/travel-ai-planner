import 'package:flutter/material.dart';

import 'hotel_options_page.dart';
import 'itinerary_page.dart';
import 'place_options_page.dart';
import 'transport_options_page.dart';
import '../models/hotel.dart';
import '../models/place.dart';
import '../models/transport.dart';
import '../services/api_service.dart';
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
  List<Transport> selectedOutboundTransports = [];
  List<Transport> selectedReturnTransports = [];

  Hotel? selectedHotel;

  List<Place> selectedPlaces = [];

  String foodPreference = 'Mixed';

  final List<String> foodPreferences = [
    'Fast food',
    'Budget restaurant',
    'Mid-range restaurant',
    'Mixed',
  ];

  bool isLoadingTransport = true;
  bool isLoadingHotel = true;
  bool isLoadingPlaces = true;

  Map<String, dynamic>? budget;
  bool isLoadingBudget = true;

  @override
  void initState() {
    super.initState();

    final savedFoodPreference = widget.trip['food_preference'];

    if (savedFoodPreference != null &&
        foodPreferences.contains(savedFoodPreference)) {
      foodPreference = savedFoodPreference;
    }

    loadSelectedTransports();
    loadSelectedHotel();
    loadSelectedPlaces();
    loadBudget();
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
        selectedOutboundTransports = transports
            .where((transport) => transport.direction == 'outbound')
            .toList();

        selectedReturnTransports = transports
            .where((transport) => transport.direction == 'return')
            .toList();

        isLoadingTransport = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingTransport = false;
      });
    }
  }

  Future<bool> saveTransport(Transport transport) async {
    final tripId = widget.trip['id'];

    try {
      await TransportService.createTransport(
        tripId: tripId,
        transport: transport,
      );

      return true;
    } catch (e) {
      if (!mounted) return false;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to save transport: $e')));

      return false;
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

    for (final oldTransport in selectedOutboundTransports) {
      if (oldTransport.type != 'Transfer') {
        await TransportService.deleteTransport(
          tripId: widget.trip['id'],
          transportId: oldTransport.id!,
        );
      }
    }

    final saved = await saveTransport(transport);

    if (!saved || !context.mounted) {
      return;
    }

    await loadSelectedTransports();
    await loadBudget();
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

    for (final oldTransport in selectedReturnTransports) {
      if (oldTransport.type != 'Transfer') {
        await TransportService.deleteTransport(
          tripId: widget.trip['id'],
          transportId: oldTransport.id!,
        );
      }
    }

    final saved = await saveTransport(transport);

    if (!saved || !context.mounted) {
      return;
    }

    await loadSelectedTransports();
    await loadBudget();
  }

  // =========================
  // TRANSPORT CARD
  // =========================

  IconData getTransportIcon(String type) {
    switch (type) {
      case 'Flight':
        return Icons.flight;

      case 'Bus':
        return Icons.directions_bus;

      case 'Train':
        return Icons.train;

      case 'Transfer':
        return Icons.directions_car;

      default:
        return Icons.directions_transit;
    }
  }

  Widget buildTransportCard(
    Transport transport, {
    required VoidCallback onChange,
  }) {
    final bool isReturn = transport.direction == 'return';

    final String departureCity = isReturn
        ? widget.trip['destination']
        : widget.trip['origin'];

    final String arrivalCity = isReturn
        ? widget.trip['origin']
        : widget.trip['destination'];

    String formatLocation(String city, String location) {
      if (transport.type == 'Flight' &&
          location.length == 3 &&
          location == location.toUpperCase()) {
        return '$city ($location)';
      }

      return location;
    }

    final String departureLabel = formatLocation(
      departureCity,
      transport.departureLocation,
    );

    final String arrivalLabel = formatLocation(
      arrivalCity,
      transport.arrivalLocation,
    );

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
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
              child: Icon(
                getTransportIcon(transport.type),
                color: Colors.blue,
                size: 28,
              ),
            ),

            const SizedBox(width: 16),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              departureLabel,
                              softWrap: true,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 2),

                            const Text(
                              '↓',
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 2),

                            Text(
                              arrivalLabel,
                              softWrap: true,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(width: 12),

                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${transport.destinationPrice} '
                            '${transport.destinationCurrency}',
                            textAlign: TextAlign.right,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),

                          const SizedBox(height: 2),

                          Text(
                            '${transport.userPrice} '
                            '${transport.userCurrency}',
                            textAlign: TextAlign.right,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey.shade600,
                            ),
                          ),

                          const SizedBox(height: 8),

                          OutlinedButton(
                            onPressed: onChange,
                            child: const Text('Change'),
                          ),
                        ],
                      ),
                    ],
                  ),

                  const SizedBox(height: 12),

                  Text(
                    '${transport.departureDate} → '
                    '${transport.arrivalDate}',
                    style: const TextStyle(fontSize: 14),
                  ),

                  const SizedBox(height: 4),

                  Text(
                    '${transport.departureTime} → '
                    '${transport.arrivalTime}',
                    style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                  ),

                  const SizedBox(height: 4),

                  Text(
                    transport.duration,
                    style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
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

      await loadBudget();

      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Hotel saved')));
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to save hotel: $e')));
    }
  }

  // =========================
  // BUDGET
  // =========================

  Future<void> loadBudget() async {
    try {
      final tripId = widget.trip['id'];

      final data = await ApiService.getBudget(tripId: tripId);

      if (!mounted) {
        return;
      }

      setState(() {
        budget = data;
        isLoadingBudget = false;
      });
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        isLoadingBudget = false;
      });
    }
  }

  Widget _buildBudgetRow(String title, dynamic value, {bool isTotal = false}) {
    if (value == null) {
      return const SizedBox.shrink();
    }

    final amount = value['amount'];
    final currency = value['currency'];

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: TextStyle(
              fontSize: isTotal ? 16 : 14,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            '${amount.toStringAsFixed(2)} $currency',
            style: TextStyle(
              fontSize: isTotal ? 16 : 14,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ],
      ),
    );
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
      await PlaceService.deletePlaces(tripId);

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
  // PLACE CARD
  // =========================

  Widget buildPlaceCard(Place place) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          children: [
            Expanded(
              child: Text(
                place.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),

            IconButton(
              icon: const Icon(Icons.close, size: 18),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
              onPressed: () async {
                if (place.id == null) {
                  return;
                }

                final tripId = widget.trip['id'];

                try {
                  await PlaceService.deletePlace(
                    tripId: tripId,
                    placeId: place.id!,
                  );

                  if (!mounted) return;

                  setState(() {
                    selectedPlaces.remove(place);
                  });
                } catch (e) {
                  if (!mounted) return;

                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to delete place: $e')),
                  );
                }
              },
            ),
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

            const SizedBox(height: 24),

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
            else if (selectedOutboundTransports.isNotEmpty)
              ...selectedOutboundTransports.map(
                (transport) => buildTransportCard(
                  transport,
                  onChange: chooseOutboundTransport,
                ),
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
            else if (selectedReturnTransports.isNotEmpty)
              ...selectedReturnTransports.map(
                (transport) => buildTransportCard(
                  transport,
                  onChange: chooseReturnTransport,
                ),
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
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        selectedHotel!.name,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
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
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.grey.shade600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),

                                const SizedBox(width: 12),

                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '${selectedHotel!.destinationPrice} '
                                      '${selectedHotel!.destinationCurrency}',
                                      style: const TextStyle(
                                        fontSize: 20,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),

                                    const SizedBox(height: 2),

                                    Text(
                                      '${selectedHotel!.userPrice} '
                                      '${selectedHotel!.userCurrency}',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: Colors.grey.shade600,
                                      ),
                                    ),

                                    const SizedBox(height: 8),

                                    OutlinedButton(
                                      onPressed: chooseHotel,
                                      child: const Text('Change'),
                                    ),
                                  ],
                                ),
                              ],
                            ),

                            const SizedBox(height: 12),

                            Text(
                              '${selectedHotel!.checkIn.day.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkIn.month.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkIn.year}'
                              ' → '
                              '${selectedHotel!.checkOut.day.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkOut.month.toString().padLeft(2, '0')}.'
                              '${selectedHotel!.checkOut.year}',
                              style: const TextStyle(fontSize: 14),
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
            else if (selectedPlaces.isNotEmpty) ...[
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: selectedPlaces.length,
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 6,
                  childAspectRatio: 3.5,
                ),
                itemBuilder: (context, index) {
                  return buildPlaceCard(selectedPlaces[index]);
                },
              ),

              const SizedBox(height: 8),

              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: choosePlaces,
                  child: const Text('Change places'),
                ),
              ),
            ] else
              ElevatedButton(
                onPressed: choosePlaces,
                child: const Text('Choose places'),
              ),

            const SizedBox(height: 24),

            // =========================
            // FOOD
            // =========================
            const Text(
              'Food',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            DropdownButtonFormField<String>(
              initialValue: foodPreference,
              decoration: InputDecoration(
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
              ),
              items: foodPreferences.map((preference) {
                return DropdownMenuItem<String>(
                  value: preference,
                  child: Text(preference),
                );
              }).toList(),
              onChanged: (value) async {
                if (value == null) {
                  return;
                }

                final tripId = widget.trip['id'];

                try {
                  await ApiService.updateFoodPreference(
                    tripId: tripId,
                    foodPreference: value,
                  );

                  await loadBudget();

                  if (!mounted) {
                    return;
                  }

                  setState(() {
                    foodPreference = value;
                    widget.trip['food_preference'] = value;
                  });
                } catch (e) {
                  if (!mounted) {
                    return;
                  }

                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Failed to save food preference: $e'),
                    ),
                  );
                }
              },
            ),

            const SizedBox(height: 24),

            // =========================
            // BUDGET
            // =========================
            const Text(
              'Budget',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            if (isLoadingBudget)
              const Center(child: CircularProgressIndicator())
            else if (budget != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildBudgetRow('Transport', budget!['transport']),

                      _buildBudgetRow('Hotel', budget!['hotel']),

                      _buildBudgetRow('Food', budget!['food']),

                      _buildBudgetRow(
                        'Local transportation',
                        budget!['local_transportation'],
                      ),

                      _buildBudgetRow(
                        'Activities & trips',
                        budget!['activities_and_trips'],
                      ),

                      const Divider(),

                      _buildBudgetRow('Total', budget!['total'], isTotal: true),

                      const SizedBox(height: 8),

                      _buildBudgetRow(
                        'Total in your currency',
                        budget!['user_total'],
                        isTotal: true,
                      ),

                      const SizedBox(height: 8),

                      const Text(
                        'Budget is an estimate. Actual prices may vary depending on provider availability, current rates, exchange rates, food spending and selected activities.',
                        style: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
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
