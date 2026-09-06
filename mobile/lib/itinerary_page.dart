import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ItineraryPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const ItineraryPage({
    super.key,
    required this.trip,
  });

  @override
  State<ItineraryPage> createState() => _ItineraryPageState();
}

class _ItineraryPageState extends State<ItineraryPage> {
  bool isLoading = true;
  String? errorMessage;
  List<dynamic> itinerary = [];

  @override
  void initState() {
    super.initState();
    loadItinerary();
  }

  Future<void> loadItinerary() async {
    final tripId = widget.trip['id'];

    final url = Uri.parse(
      'http://10.0.2.2:8000/api/trips/$tripId/itinerary',
    );

    try {
      final response = await http.get(url);

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        setState(() {
          itinerary = data['itinerary'];
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage =
              'Server error: ${response.statusCode}';
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

  Widget buildActivity(
    String section,
    String text,
  ) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            getActivityIcon(section),
            size: 22,
            color: Colors.blue,
          ),
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
                  style: TextStyle(
                    fontSize: 15,
                    color: Colors.grey.shade700,
                  ),
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
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text(
                      errorMessage!,
                      textAlign: TextAlign.center,
                    ),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
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
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade600,
                        ),
                      ),

                      const SizedBox(height: 28),

                      ...itinerary.map(
                        (day) => Card(
                          margin: const EdgeInsets.only(
                            bottom: 20,
                          ),
                          elevation: 2,
                          shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(16),
                          ),
                          child: Padding(
                            padding:
                                const EdgeInsets.all(18),
                            child: Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Day ${day['day']}',
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight:
                                        FontWeight.bold,
                                  ),
                                ),

                                const SizedBox(height: 4),

                                Text(
                                  day['title'],
                                  style: TextStyle(
                                    fontSize: 16,
                                    color:
                                        Colors.grey.shade600,
                                  ),
                                ),

                                const SizedBox(height: 20),

                                buildActivity(
                                  'morning',
                                  day['morning'],
                                ),

                                buildActivity(
                                  'lunch',
                                  day['lunch'],
                                ),

                                buildActivity(
                                  'afternoon',
                                  day['afternoon'],
                                ),

                                buildActivity(
                                  'evening',
                                  day['evening'],
                                ),
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