import 'dart:convert';

import '../api_config.dart';
import '../widgets/itinerary_map.dart';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ItineraryPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final bool includeArrivalDayActivities;
  final bool includeDepartureDayActivities;

  const ItineraryPage({
    super.key,
    required this.trip,
    required this.includeArrivalDayActivities,
    required this.includeDepartureDayActivities,
  });

  @override
  State<ItineraryPage> createState() => _ItineraryPageState();
}

class _ItineraryPageState extends State<ItineraryPage> {
  bool isLoading = true;
  String? errorMessage;

  List<dynamic> itinerary = [];

  Map<String, dynamic>? hotel;
  List<Map<String, dynamic>> mapPlaces = [];
  Set<int> selectedDays = {};

  @override
  void initState() {
    super.initState();
    loadItinerary();
  }

  List<Map<String, dynamic>> get filteredMapPlaces {
    if (selectedDays.isEmpty) {
      return mapPlaces;
    }

    final result = <Map<String, dynamic>>[];

    for (final day in itinerary) {
      if (day is! Map) {
        continue;
      }

      final dayNumber = day['day'];

      if (dayNumber is! int || !selectedDays.contains(dayNumber)) {
        continue;
      }

      final places = day['map_places'];

      if (places is List) {
        result.addAll(
          places.whereType<Map>().map(
            (place) => Map<String, dynamic>.from(place),
          ),
        );
      }
    }

    // Убираем повторяющиеся места,
    // если одно место оказалось выбрано в нескольких днях.
    final uniquePlaces = <String, Map<String, dynamic>>{};

    for (final place in result) {
      final key = [
        place['name'],
        place['latitude'],
        place['longitude'],
      ].join('|');

      uniquePlaces[key] = place;
    }

    return uniquePlaces.values.toList();
  }

  List<Map<String, dynamic>> get filteredMapAirports {
    final airports = <Map<String, dynamic>>[];

    for (final day in itinerary) {
      if (day is! Map) {
        continue;
      }

      final dayNumber = day['day'];

      if (selectedDays.isNotEmpty &&
          (dayNumber is! int || !selectedDays.contains(dayNumber))) {
        continue;
      }

      final arrivalAirport = day['arrival_airport'];

      if (arrivalAirport is Map) {
        airports.add({
          ...Map<String, dynamic>.from(arrivalAirport),
          'label': 'Arrival airport',
        });
      }

      final departureAirport = day['departure_airport'];

      if (departureAirport is Map) {
        airports.add({
          ...Map<String, dynamic>.from(departureAirport),
          'label': 'Departure airport',
        });
      }
    }

    final uniqueAirports = <String, Map<String, dynamic>>{};

    for (final airport in airports) {
      final key = [
        airport['code'],
        airport['latitude'],
        airport['longitude'],
      ].join('|');

      if (!uniqueAirports.containsKey(key)) {
        uniqueAirports[key] = airport;
      } else {
        final existing = uniqueAirports[key]!;

        final existingLabel = existing['label'];
        final currentLabel = airport['label'];

        if (existingLabel != currentLabel) {
          existing['label'] = 'Airport';
        }
      }
    }

    return uniqueAirports.values.toList();
  }

  Future<void> loadItinerary() async {
    final tripId = widget.trip['id'];

    final url = Uri.parse('${ApiConfig.baseUrl}/api/trips/$tripId/itinerary')
        .replace(
          queryParameters: {
            'include_arrival_day': widget.includeArrivalDayActivities
                .toString(),
            'include_departure_day': widget.includeDepartureDayActivities
                .toString(),
          },
        );

    try {
      final response = await http.get(url);

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        final loadedItinerary = data['itinerary'] is List
            ? List<dynamic>.from(data['itinerary'])
            : <dynamic>[];

        final loadedHotel = data['hotel'] is Map
            ? Map<String, dynamic>.from(data['hotel'])
            : null;

        final loadedMapPlaces = <Map<String, dynamic>>[];

        for (final day in loadedItinerary) {
          if (day is! Map) {
            continue;
          }

          final places = day['map_places'];

          if (places is! List) {
            continue;
          }

          for (final place in places) {
            if (place is Map) {
              loadedMapPlaces.add(Map<String, dynamic>.from(place));
            }
          }
        }

        setState(() {
          itinerary = loadedItinerary;
          hotel = loadedHotel;
          mapPlaces = loadedMapPlaces;
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = 'Server error: ${response.statusCode}';
          isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) {
        return;
      }

      setState(() {
        errorMessage = 'Connection error: $e';
        isLoading = false;
      });
    }
  }

  IconData getActivityIcon(String section) {
    switch (section) {
      case 'morning':
        return Icons.wb_sunny_outlined;
      case 'lunch':
        return Icons.restaurant_outlined;
      case 'afternoon':
        return Icons.explore_outlined;
      case 'evening':
        return Icons.nightlight_outlined;
      default:
        return Icons.circle_outlined;
    }
  }

  String getSectionTitle(String section) {
    switch (section) {
      case 'morning':
        return 'Morning';
      case 'lunch':
        return 'Lunch';
      case 'afternoon':
        return 'Afternoon';
      case 'evening':
        return 'Evening';
      default:
        return section;
    }
  }

  Widget buildActivity(String section, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(getActivityIcon(section), size: 22, color: Colors.blue),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  getSectionTitle(section),
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  text,
                  style: TextStyle(fontSize: 15, color: Colors.grey.shade700),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'AI Itinerary',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Text(errorMessage!, textAlign: TextAlign.center),
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    destination,
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Your personalized trip itinerary',
                    style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 28),

                  if (hotel != null || mapPlaces.isNotEmpty) ...[
                    const Text(
                      'Map',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),

                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          ChoiceChip(
                            label: const Text('All days'),
                            selected: selectedDays.isEmpty,
                            onSelected: (_) {
                              setState(() {
                                selectedDays.clear();
                              });
                            },
                          ),
                          const SizedBox(width: 8),

                          ...itinerary.map((day) {
                            final dayNumber = day['day'] as int;

                            return Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ChoiceChip(
                                label: Text('Day $dayNumber'),
                                selected: selectedDays.contains(dayNumber),
                                onSelected: (selected) {
                                  setState(() {
                                    if (selected) {
                                      selectedDays.add(dayNumber);
                                    } else {
                                      selectedDays.remove(dayNumber);
                                    }
                                  });
                                },
                              ),
                            );
                          }),
                        ],
                      ),
                    ),

                    const SizedBox(height: 12),

                    ItineraryMap(
                      hotel: hotel,
                      places: filteredMapPlaces,
                      airports: filteredMapAirports,
                    ),

                    const SizedBox(height: 28),
                  ],

                  ...itinerary.map(
                    (day) => Card(
                      margin: const EdgeInsets.only(bottom: 20),
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Day ${day['day']}',
                              style: const TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              day['title'],
                              style: TextStyle(
                                fontSize: 16,
                                color: Colors.grey.shade600,
                              ),
                            ),
                            const SizedBox(height: 20),
                            buildActivity('morning', day['morning']),
                            buildActivity('lunch', day['lunch']),
                            buildActivity('afternoon', day['afternoon']),
                            buildActivity('evening', day['evening']),
                          ],
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
