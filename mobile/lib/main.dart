import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

import 'pages/create_trip_page.dart';
import 'pages/trip_details_page.dart';
import 'services/api_service.dart';

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
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
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
  String appVersion = '';

  bool isLoadingTrips = false;

  List<dynamic> trips = [];

  @override
  void initState() {
    super.initState();

    getTrips();
    loadAppVersion();
  }

  Future<void> loadAppVersion() async {
    final packageInfo = await PackageInfo.fromPlatform();

    if (!mounted) {
      return;
    }

    setState(() {
      appVersion = packageInfo.version;
    });
  }

  Future<void> getTrips() async {
    setState(() {
      isLoadingTrips = true;
    });

    try {
      final result = await ApiService.getTrips();

      if (!mounted) {
        return;
      }

      setState(() {
        trips = result;
      });

      print('API TRIPS RESULT: $result');
      print(
        'TRIP 30 CURRENCY: ${result.firstWhere((trip) => trip['id'] == 30, orElse: () => {})['user_currency']}',
      );
    } finally {
      if (mounted) {
        setState(() {
          isLoadingTrips = false;
        });
      }
    }
  }

  Future<void> createTrip() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const CreateTripPage()),
    );

    if (result == true && mounted) {
      await getTrips();
    }
  }

  Future<void> deleteTrip(Map<String, dynamic> trip) async {
    final tripId = trip['id'];

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete trip?'),
          content: Text(
            '${trip['origin']} → ${trip['destination']}\n\n'
            'This trip and all its saved data will be deleted.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(false);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(context).pop(true);
              },
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) {
      return;
    }

    try {
      await ApiService.deleteTrip(tripId);

      if (!mounted) {
        return;
      }

      setState(() {
        trips.removeWhere((item) => item['id'] == tripId);
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Trip deleted.')));
    } catch (e) {
      print('Delete trip error: $e');

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to delete trip: $e')));
    }
  }

  String formatApiDate(String date) {
    final parts = date.split('-');

    if (parts.length != 3) {
      return date;
    }

    return '${parts[2]}.${parts[1]}.${parts[0]}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Travel AI Planner',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 2),
            Text(
              'v$appVersion',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Stack(
          children: [
            if (isLoadingTrips)
              const Center(child: CircularProgressIndicator())
            else if (trips.isEmpty)
              const Center(
                child: Text(
                  'No trips yet',
                  style: TextStyle(fontSize: 20, color: Colors.grey),
                ),
              )
            else
              ListView(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 100),
                children: [
                  const Text(
                    'My Trips',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 16),

                  ...trips.map(
                    (trip) => Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      elevation: 2,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () async {
                          print('Selected trip: $trip');

                          await Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => TripDetailsPage(
                                trip: Map<String, dynamic>.from(trip),
                              ),
                            ),
                          );

                          if (mounted) {
                            await getTrips();
                          }
                        },
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
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
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
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
                                          style: const TextStyle(fontSize: 14),
                                        ),

                                        const Spacer(),

                                        const Icon(
                                          Icons.arrow_forward,
                                          size: 18,
                                        ),

                                        const Spacer(),

                                        Text(
                                          formatApiDate(trip['end_date']),
                                          style: const TextStyle(fontSize: 14),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 10),

                              Row(
                                children: [
                                  const Icon(Icons.people_outline, size: 18),

                                  const SizedBox(width: 8),

                                  Text(
                                    '${trip['travelers']} '
                                    '${trip['travelers'] == 1 ? 'traveler' : 'travelers'}',
                                  ),

                                  const Spacer(),

                                  const SizedBox.shrink(),

                                  const SizedBox(width: 8),

                                  IconButton(
                                    tooltip: 'Delete trip',
                                    onPressed: () {
                                      deleteTrip(
                                        Map<String, dynamic>.from(trip),
                                      );
                                    },
                                    icon: const Icon(
                                      Icons.delete_outline,
                                      color: Colors.red,
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
                ],
              ),

            Positioned(
              left: 20,
              bottom: 20,
              child: FloatingActionButton(
                onPressed: createTrip,
                tooltip: 'Create trip',
                child: const Icon(Icons.add),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
