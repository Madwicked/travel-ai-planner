import 'dart:convert';
import 'api_config.dart';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'transport_options_page.dart';
import 'hotel_options_page.dart';
import 'itinerary_page.dart';
import 'place_options_page.dart';

String formatApiDate(String date) {
  final parts = date.split('-');

  if (parts.length != 3) {
    return date;
  }

  return '${parts[2]}.${parts[1]}.${parts[0]}';
}

class TripDetailsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const TripDetailsPage({
    super.key,
    required this.trip,
  });

  @override
  State<TripDetailsPage> createState() => _TripDetailsPageState();
}

class _TripDetailsPageState extends State<TripDetailsPage> {
  Map<String, dynamic>? selectedOutboundTransport;
  Map<String, dynamic>? selectedReturnTransport;
  Map<String, dynamic>? selectedHotel;

  List<Map<String, dynamic>> selectedPlaces = [];

  bool isLoadingTransport = true;
  bool isLoadingHotel = true;

  IconData getTransportIcon(String type) {
    switch (type) {
      case 'Flight':
        return Icons.flight;
      case 'Bus':
        return Icons.directions_bus;
      case 'Train':
        return Icons.train;
      default:
        return Icons.directions_transit;
    }
  }

  IconData getPlaceIcon(String category) {
    switch (category) {
      case 'Culture':
        return Icons.account_balance;
      case 'Nature':
        return Icons.park;
      case 'Sightseeing':
        return Icons.photo_camera;
      default:
        return Icons.place;
    }
  }

  Future<void> loadSelectedTransports() async {
    final tripId = widget.trip['id'];

    try {
      final response = await http.get(
        Uri.parse(
          '${ApiConfig.baseUrl}/api/trips/$tripId/transports',
        ),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to load transports',
        );
      }

      final data = jsonDecode(response.body);

      final transports =
          List<Map<String, dynamic>>.from(
        data['transports'],
      );

      final outboundTransports = transports
          .where(
            (transport) =>
                transport['direction'] == 'outbound',
          )
          .toList();

      final returnTransports = transports
          .where(
            (transport) =>
                transport['direction'] == 'return',
          )
          .toList();

      if (!mounted) return;

      setState(() {
        if (outboundTransports.isNotEmpty) {
          selectedOutboundTransport =
              outboundTransports.last;
        }

        if (returnTransports.isNotEmpty) {
          selectedReturnTransport =
              returnTransports.last;
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

  Future<void> loadSelectedHotel() async {
    final tripId = widget.trip['id'];

    try {
      final response = await http.get(
        Uri.parse(
          '${ApiConfig.baseUrl}/api/trips/$tripId/hotels',
        ),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to load hotel',
        );
      }

      final data = jsonDecode(response.body);

      final hotels =
          List<Map<String, dynamic>>.from(
        data['hotels'],
      );

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

  Future<void> loadSelectedPlaces() async {
  final tripId = widget.trip['id'];

  try {
    final response = await http.get(
      Uri.parse(
        '${ApiConfig.baseUrl}/api/trips/$tripId/places',
      ),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to load places',
      );
    }

    final data = jsonDecode(response.body);

    final places =
        List<Map<String, dynamic>>.from(
      data['places'],
    );

    if (!mounted) return;

    setState(() {
      selectedPlaces = places;
    });
  } catch (e) {
    // Places are optional, so we don't block the page
    // if loading them fails.
  }
}

  Future<void> saveTransport(
    Map<String, dynamic> transport,
    String direction,
  ) async {
    final tripId = widget.trip['id'];

    final response = await http.post(
      Uri.parse(
        '${ApiConfig.baseUrl}/api/trips/$tripId/transports',
      ),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'direction': direction,
        'transport_type': transport['type'],
        'transport_price': transport['price'],
        'transport_duration': transport['duration'],
        'departure_date': transport['departure_date'],
        'departure_time': transport['departure_time'],
        'departure_location':
            transport['departure_location'],
        'arrival_date': transport['arrival_date'],
        'arrival_time': transport['arrival_time'],
        'arrival_location':
            transport['arrival_location'],
      }),
    );

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to save transport: ${response.body}',
      );
    }
  }

  Future<void> chooseOutboundTransport() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TransportOptionsPage(
          trip: widget.trip,
        ),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport =
        Map<String, dynamic>.from(result);

    try {
      await saveTransport(
        transport,
        'outbound',
      );

      if (!context.mounted) return;

      setState(() {
        selectedOutboundTransport = transport;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Outbound transport saved'),
        ),
      );
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to save transport: $e',
          ),
        ),
      );
    }
  }

  Future<void> chooseReturnTransport() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TransportOptionsPage(
          trip: {
            ...widget.trip,
            'return_transport': true,
          },
        ),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport =
        Map<String, dynamic>.from(result);

    try {
      await saveTransport(
        transport,
        'return',
      );

      if (!context.mounted) return;

      setState(() {
        selectedReturnTransport = transport;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Return transport saved'),
        ),
      );
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to save return transport: $e',
          ),
        ),
      );
    }
  }

  Future<void> chooseHotel() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => HotelOptionsPage(
          trip: widget.trip,
        ),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final hotel =
        Map<String, dynamic>.from(result);

    final tripId = widget.trip['id'];

    try {
      final response = await http.post(
        Uri.parse(
          '${ApiConfig.baseUrl}/api/trips/$tripId/hotels',
        ),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'name': hotel['name'],
          'city': hotel['city'],
          'address': hotel['address'],
          'price_per_night':
              hotel['price_per_night'],
          'nights': hotel['nights'],
          'total_price':
              hotel['total_price'],
          'check_in': hotel['check_in'],
          'check_out': hotel['check_out'],
        }),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to save hotel: ${response.body}',
        );
      }

      if (!context.mounted) return;

      setState(() {
        selectedHotel = hotel;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Hotel saved'),
        ),
      );
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to save hotel: $e',
          ),
        ),
      );
    }
  }

  Future<void> choosePlaces() async {
  final result = await Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => PlaceOptionsPage(
        trip: widget.trip,
      ),
    ),
  );

  if (result == null || !context.mounted) {
    return;
  }

  final places =
      List<Map<String, dynamic>>.from(result);

      

  final tripId = widget.trip['id'];

  await http.delete(
    Uri.parse(
      '${ApiConfig.baseUrl}/api/trips/$tripId/places',
    ),
  );

  try {
    for (final place in places) {
      final response = await http.post(
        Uri.parse(
          '${ApiConfig.baseUrl}/api/trips/$tripId/places',
        ),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'external_id': place['external_id'],
          'source': place['source'],
          'name': place['name'],
          'city': place['city'],
          'category': place['category'],
          'address': place['address'],
          'latitude': place['latitude'],
          'longitude': place['longitude'],
          'rating': place['rating'],
          'opening_hours': place['opening_hours'],
          'opening_time': place['opening_time'],
          'closing_time': place['closing_time'],
          'visit_duration': place['visit_duration'],
        }),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to save place: ${response.body}',
        );
      }
    }

    if (!context.mounted) return;

    setState(() {
      selectedPlaces = places;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '${places.length} '
          '${places.length == 1 ? 'place' : 'places'} saved',
        ),
      ),
    );
  } catch (e) {
    if (!context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Failed to save places: $e',
        ),
      ),
    );
  }
}

  Widget buildTransportCard(
    Map<String, dynamic> transport,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Icon(
              getTransportIcon(
                transport['type'] as String,
              ),
              size: 32,
              color: Colors.blue,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    transport['type'] as String,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${formatApiDate(
                      transport['departure_date'],
                    )} '
                    '${transport['departure_time']}',
                    style: const TextStyle(
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    transport['departure_location'] ??
                        '',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${formatApiDate(
                      transport['arrival_date'],
                    )} '
                    '${transport['arrival_time']}',
                    style: const TextStyle(
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    transport['arrival_location'] ??
                        '',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    transport['duration'] as String,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '€${transport['price']}',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildPlaceCard(
    Map<String, dynamic> place,
  ) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Icon(
              getPlaceIcon(
                place['category'] as String,
              ),
              size: 30,
              color: Colors.blue,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    place['name'] as String,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    place['category'] as String,
                    style: const TextStyle(
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    place['address'] as String,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Open: '
                    '${place['opening_time']}'
                    '–'
                    '${place['closing_time']}',
                    style: const TextStyle(
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Visit: '
                    '${place['visit_duration']}',
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
    );
  }

  @override
  void initState() {
    super.initState();
    loadSelectedTransports();
    loadSelectedHotel();
    loadSelectedPlaces();
  }

  @override
  Widget build(BuildContext context) {
    final trip = widget.trip;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Trip Details',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            Text(
              trip['destination'],
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 24),

            Row(
              children: [
                const Icon(
                  Icons.calendar_today_outlined,
                ),
                const SizedBox(width: 12),
                Text(
                  '${formatApiDate(trip['start_date'])} → '
                  '${formatApiDate(trip['end_date'])}',
                  style: const TextStyle(
                    fontSize: 16,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            Row(
              children: [
                const Icon(Icons.people_outline),
                const SizedBox(width: 12),
                Text(
                  '${trip['travelers']} '
                  '${trip['travelers'] == 1 ? 'traveler' : 'travelers'}',
                  style: const TextStyle(
                    fontSize: 16,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            Row(
              children: [
                const Icon(Icons.euro),
                const SizedBox(width: 12),
                Text(
                  '€${trip['budget']}',
                  style: const TextStyle(
                    fontSize: 16,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 28),

            const Text(
              'Interests',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            Text(
              trip['interests'] ??
                  'No interests specified',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade700,
              ),
            ),

            const SizedBox(height: 28),

            if (isLoadingTransport)
              const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    vertical: 20,
                  ),
                  child: CircularProgressIndicator(),
                ),
              ),

            if (!isLoadingTransport) ...[
              const Text(
                'Outbound Transport',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 12),

              if (selectedOutboundTransport !=
                  null)
                buildTransportCard(
                  selectedOutboundTransport!,
                ),

              const SizedBox(height: 12),

              SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton.icon(
                  onPressed:
                      chooseOutboundTransport,
                  icon: Icon(
                    selectedOutboundTransport ==
                            null
                        ? Icons.directions_transit
                        : Icons.swap_horiz,
                  ),
                  label: Text(
                    selectedOutboundTransport ==
                            null
                        ? 'Choose Outbound Transport'
                        : 'Change Outbound Transport',
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 28),

              const Text(
                'Return Transport',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 12),

              if (selectedReturnTransport !=
                  null)
                buildTransportCard(
                  selectedReturnTransport!,
                ),

              const SizedBox(height: 12),

              SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton.icon(
                  onPressed:
                      chooseReturnTransport,
                  icon: Icon(
                    selectedReturnTransport == null
                        ? Icons.keyboard_return
                        : Icons.swap_horiz,
                  ),
                  label: Text(
                    selectedReturnTransport == null
                        ? 'Choose Return Transport'
                        : 'Change Return Transport',
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],

            const SizedBox(height: 28),

            const Text(
              'Hotel',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            if (isLoadingHotel)
              const Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    vertical: 20,
                  ),
                  child: CircularProgressIndicator(),
                ),
              ),

            if (!isLoadingHotel &&
                selectedHotel != null)
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius:
                      BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.hotel,
                        size: 32,
                        color: Colors.blue,
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            Text(
                              selectedHotel!['name']
                                  as String,
                              style:
                                  const TextStyle(
                                fontSize: 18,
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              selectedHotel!['city']
                                  as String,
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              selectedHotel!['address']
                                  as String,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),
                            const SizedBox(height: 10),
                            Text(
                              '${formatApiDate(
                                selectedHotel![
                                    'check_in'],
                              )} → '
                              '${formatApiDate(
                                selectedHotel![
                                    'check_out'],
                              )}',
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${selectedHotel!['nights']} '
                              '${selectedHotel!['nights'] == 1 ? 'night' : 'nights'}',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment:
                            CrossAxisAlignment.end,
                        children: [
                          Text(
                            '€${selectedHotel!['total_price']}',
                            style:
                                const TextStyle(
                              fontSize: 18,
                              fontWeight:
                                  FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '€${selectedHotel!['price_per_night']}/night',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors
                                  .grey
                                  .shade600,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              height: 54,
              child: FilledButton.icon(
                onPressed: chooseHotel,
                icon: Icon(
                  selectedHotel == null
                      ? Icons.hotel
                      : Icons.swap_horiz,
                ),
                label: Text(
                  selectedHotel == null
                      ? 'Choose Hotel'
                      : 'Change Hotel',
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 28),

            const Text(
              'Places to Visit',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 12),

            if (selectedPlaces.isNotEmpty) ...[
              ...selectedPlaces.map(
                (place) => Padding(
                  padding: const EdgeInsets.only(
                    bottom: 12,
                  ),
                  child: buildPlaceCard(place),
                ),
              ),
            ],

            SizedBox(
              width: double.infinity,
              height: 54,
              child: FilledButton.icon(
                onPressed: choosePlaces,
                icon: Icon(
                  selectedPlaces.isEmpty
                      ? Icons.place
                      : Icons.swap_horiz,
                ),
                label: Text(
                  selectedPlaces.isEmpty
                      ? 'Choose Places'
                      : 'Change Places',
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 40),

            SizedBox(
              width: double.infinity,
              height: 54,
              child: FilledButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) =>
                          ItineraryPage(
                        trip: trip,
                      ),
                    ),
                  );
                },
                icon: const Icon(
                  Icons.auto_awesome,
                ),
                label: const Text(
                  'Generate AI Itinerary',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}