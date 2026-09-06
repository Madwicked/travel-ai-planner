import 'dart:convert';
import 'api_config.dart';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'trip_details_page.dart';

void main() {
  runApp(const TravelAiPlannerApp());
}

class TravelAiPlannerApp extends StatelessWidget {
  const TravelAiPlannerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Travel AI Planner',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
        ),
      ),
      home: const TripPlannerPage(),
    );
  }
}

class TripPlannerPage extends StatefulWidget {
  const TripPlannerPage({super.key});

  @override
  State<TripPlannerPage> createState() => _TripPlannerPageState();
}

class _TripPlannerPageState extends State<TripPlannerPage> {
  final originController = TextEditingController();
  final destinationController = TextEditingController();
  final budgetController = TextEditingController();

  DateTime? startDate;
  DateTime? endDate;

  int travelers = 1;

  bool isLoading = false;
  bool isLoadingTrips = false;

  List<dynamic> trips = [];

  final interests = <String>[
    '🏛️ Culture',
    '🍴 Food',
    '🏖️ Beach',
    '🌲 Nature',
    '🎉 Nightlife',
    '🛍️ Shopping',
  ];

  final selectedInterests = <String>{};

  @override
  void initState() {
    super.initState();
    getTrips();
  }

  Future<void> selectDate(bool isStartDate) async {
    final result = await showDialog<DateTime>(
      context: context,
      builder: (context) {
        return Dialog(
          child: CalendarDatePicker(
            initialDate: isStartDate
                ? (startDate ?? DateTime.now())
                : (endDate ?? startDate ?? DateTime.now()),
            firstDate: DateTime.now(),
            lastDate: DateTime.now().add(
              const Duration(days: 730),
            ),
            onDateChanged: (date) {
              Navigator.of(context).pop(date);
            },
          ),
        );
      },
    );

    if (result == null || !mounted) {
      return;
    }

    setState(() {
      if (isStartDate) {
        startDate = result;

        if (endDate != null && endDate!.isBefore(result)) {
          endDate = null;
        }
      } else {
        endDate = result;
      }
    });
  }

  String formatDate(DateTime? date) {
    if (date == null) {
      return 'Select date';
    }

    return '${date.day.toString().padLeft(2, '0')}.'
        '${date.month.toString().padLeft(2, '0')}.'
        '${date.year}';
  }

  String formatApiDate(String date) {
  final parts = date.split('-');

  if (parts.length != 3) {
    return date;
  }

  return '${parts[2]}.${parts[1]}.${parts[0]}';
}

  Future<void> generateTrip() async {
    if (originController.text.trim().isEmpty ||
        destinationController.text.trim().isEmpty ||
        startDate == null ||
        endDate == null ||
        budgetController.text.trim().isEmpty ||
        selectedInterests.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Please fill in all fields and select at least one interest.',
          ),
        ),
      );
      return;
    }

    final budget = double.tryParse(
      budgetController.text.trim(),
    );

    if (budget == null || budget <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Please enter a valid budget.',
          ),
        ),
      );
      return;
    }

    setState(() {
      isLoading = true;
    });

    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips',
    );

    final body = {
      'origin': originController.text.trim(),
      'destination': destinationController.text.trim(),
      'start_date': startDate!.toIso8601String().split('T').first,
      'end_date': endDate!.toIso8601String().split('T').first,
      'travelers': travelers,
      'budget': budget,
      'interests': selectedInterests.toList(),
    };

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(body),
      );

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        await getTrips();

        if (!mounted) {
          return;
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Trip created! ID: ${data['trip_id']}',
            ),
          ),
        );
      } else {
        print('API error: ${response.body}');

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Server error: ${response.statusCode}',
            ),
          ),
        );
      }
    } catch (e) {
      print('Connection error: $e');

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Connection error: $e',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  Future<void> getTrips() async {
    setState(() {
      isLoadingTrips = true;
    });

    final url = Uri.parse(
      '${ApiConfig.baseUrl}/api/trips',
    );

    try {
      final response = await http.get(url);

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        setState(() {
          trips = jsonDecode(response.body);
        });

        print('Trips: $trips');
      } else {
        print('API error: ${response.body}');
      }
    } catch (e) {
      print('Connection error: $e');
    } finally {
      if (mounted) {
        setState(() {
          isLoadingTrips = false;
        });
      }
    }
  }

  @override
  void dispose() {
    originController.dispose();
    destinationController.dispose();
    budgetController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Travel AI Planner',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Plan your perfect trip ✈️',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 8),

              Text(
                'Tell us about your trip and AI will create '
                'a personalized itinerary.',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey.shade600,
                ),
              ),

              const SizedBox(height: 28),

              const Text(
  'From',
  style: TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
  ),
),

const SizedBox(height: 8),

TextField(
  controller: originController,
  decoration: InputDecoration(
    hintText: 'e.g. Belgrade, Serbia',
    prefixIcon: const Icon(
      Icons.flight_takeoff,
    ),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
    ),
  ),
),

const SizedBox(height: 20),

const Text(
  'To',
  style: TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
  ),
),

const SizedBox(height: 8),

TextField(
  controller: destinationController,
  decoration: InputDecoration(
    hintText: 'e.g. Rome, Italy',
    prefixIcon: const Icon(
      Icons.location_on_outlined,
    ),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
    ),
  ),
),

              const SizedBox(height: 20),

              const Text(
                'Travel dates',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: 8),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isLoading
                          ? null
                          : () => selectDate(true),
                      icon: const Icon(
                        Icons.calendar_today,
                      ),
                      label: Text(
                        formatDate(startDate),
                      ),
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isLoading
                          ? null
                          : () => selectDate(false),
                      icon: const Icon(
                        Icons.calendar_today,
                      ),
                      label: Text(
                        formatDate(endDate),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              const Text(
                'Travelers',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: 8),

              Container(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: Colors.grey.shade400,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  mainAxisAlignment:
                      MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      onPressed: isLoading || travelers <= 1
                          ? null
                          : () {
                              setState(() {
                                travelers--;
                              });
                            },
                      icon: const Icon(
                        Icons.remove,
                      ),
                    ),

                    Text(
                      '$travelers '
                      '${travelers == 1 ? 'traveler' : 'travelers'}',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    IconButton(
                      onPressed: isLoading
                          ? null
                          : () {
                              setState(() {
                                travelers++;
                              });
                            },
                      icon: const Icon(
                        Icons.add,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                'Budget (€)',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: 8),

              TextField(
                controller: budgetController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                  hintText: 'e.g. 1000',
                  prefixIcon: const Icon(
                    Icons.euro,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),

              const SizedBox(height: 20),

              const Text(
                'Interests',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: 10),

              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: interests.map((interest) {
                  final isSelected =
                      selectedInterests.contains(interest);

                  return FilterChip(
                    label: Text(interest),
                    selected: isSelected,
                    onSelected: isLoading
                        ? null
                        : (selected) {
                            setState(() {
                              if (selected) {
                                selectedInterests.add(
                                  interest,
                                );
                              } else {
                                selectedInterests.remove(
                                  interest,
                                );
                              }
                            });
                          },
                  );
                }).toList(),
              ),

              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton.icon(
                  onPressed: isLoading
                      ? null
                      : generateTrip,
                  icon: isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                          ),
                        )
                      : const Icon(
                          Icons.auto_awesome,
                        ),
                  label: Text(
                    isLoading
                        ? 'Generating...'
                        : 'Generate My Trip',
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 32),

              const Text(
                'My Trips',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 12),

              if (isLoadingTrips)
                const Center(
                  child: CircularProgressIndicator(),
                )
              else if (trips.isEmpty)
                const Text(
                  'No trips yet.',
                  style: TextStyle(
                    color: Colors.grey,
                  ),
                )
              else
                ...trips.map(
                  (trip) => Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    elevation: 2,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(16),
                      onTap: () {
                        print('Selected trip: $trip');
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                TripDetailsPage(
                              trip: Map<String, dynamic>.from(
                                trip,
                              ),
                            ),
                          ),
                        );
                      },
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            Row(
  crossAxisAlignment: CrossAxisAlignment.start,
  children: [
    Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Icon(
        Icons.flight_takeoff,
        color: Colors.blue,
      ),
    ),

    const SizedBox(width: 12),

    Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            trip['origin'],
            style: const TextStyle(
              fontSize: 15,
              color: Colors.grey,
            ),
          ),

          const SizedBox(height: 4),

          Row(
            children: [
              const Icon(
                Icons.arrow_downward,
                size: 18,
              ),

              const SizedBox(width: 4),

              Expanded(
                child: Text(
                  trip['destination'],
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  ],
),

                            const SizedBox(height: 16),

                            Row(
                              children: [
                                const Icon(
                                  Icons.calendar_today_outlined,
                                  size: 18,
                                ),

                                const SizedBox(width: 8),

                                Expanded(
                                  child: Row(
                                    children: [
                                      Text(
                                        formatApiDate(trip['start_date']),
                                        style: const TextStyle(
                                          fontSize: 14,
                                        ),
                                      ),

                                      const Spacer(),

                                      const Icon(
                                        Icons.arrow_forward,
                                        size: 18,
                                      ),

                                      const Spacer(),

                                      Text(
                                        formatApiDate(trip['end_date']),
                                        style: const TextStyle(
                                          fontSize: 14,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),

                            const SizedBox(height: 10),

                            Row(
                              children: [
                                const Icon(
                                  Icons.people_outline,
                                  size: 18,
                                ),

                                const SizedBox(width: 8),

                                Text(
                                  '${trip['travelers']} '
                                  '${trip['travelers'] == 1 ? 'traveler' : 'travelers'}',
                                ),

                                const Spacer(),

                                Text(
                                  '€${trip['budget']}',
                                  style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight:
                                        FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}