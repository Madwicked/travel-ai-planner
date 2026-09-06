import 'dart:convert';
import 'api_config.dart';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class TransportOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const TransportOptionsPage({
    super.key,
    required this.trip,
  });

  @override
  State<TransportOptionsPage> createState() =>
      _TransportOptionsPageState();
}

class _TransportOptionsPageState
    extends State<TransportOptionsPage> {
  List<Map<String, dynamic>> options = [];

  bool isLoading = true;
  String? errorMessage;

  bool get isReturnTransport =>
      widget.trip['return_transport'] == true;

  String formatDateForDisplay(String date) {
    final parts = date.split('-');

    if (parts.length != 3) {
      return date;
    }

    return '${parts[2]}.${parts[1]}.${parts[0]}';
  }

  Future<void> loadTransportOptions() async {
    final tripId = widget.trip['id'];

    final endpoint = isReturnTransport
        ? 'return-options'
        : 'options';

    try {
      final response = await http.get(
        Uri.parse(
          '${ApiConfig.baseUrl}/api/trips/$tripId/transports/$endpoint',
        ),
      );

      if (response.statusCode != 200) {
        throw Exception(
          'Failed to load transport options',
        );
      }

      final data = jsonDecode(response.body);

      final loadedOptions =
          List<Map<String, dynamic>>.from(
        data['options'],
      );

      if (!mounted) return;

      setState(() {
        options = loadedOptions;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage =
            'Failed to load transport options';
        isLoading = false;
      });
    }
  }

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

  @override
  void initState() {
    super.initState();
    loadTransportOptions();
  }

  @override
  Widget build(BuildContext context) {
    final origin = widget.trip['origin'];
    final destination = widget.trip['destination'];

    final from = isReturnTransport
        ? destination
        : origin;

    final to = isReturnTransport
        ? origin
        : destination;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isReturnTransport
              ? 'Return Transport'
              : 'Transport Options',
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: _buildBody(
        from,
        to,
      ),
    );
  }

  Widget _buildBody(
    String from,
    String to,
  ) {
    if (isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            errorMessage!,
            style: const TextStyle(
              fontSize: 16,
            ),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Text(
            '$from → $to',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 8),

          Text(
            isReturnTransport
                ? 'Choose how you want to get back'
                : 'Choose how you want to get there',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey.shade600,
            ),
          ),

          const SizedBox(height: 28),

          ...options.map(
            (option) => Card(
              margin: const EdgeInsets.only(
                bottom: 16,
              ),
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.circular(16),
              ),
              child: InkWell(
                borderRadius:
                    BorderRadius.circular(16),
                onTap: () {
                  Navigator.pop(
                    context,
                    option,
                  );
                },
                child: Padding(
                  padding:
                      const EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding:
                            const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.blue
                              .withOpacity(0.1),
                          borderRadius:
                              BorderRadius.circular(
                            12,
                          ),
                        ),
                        child: Icon(
                          getTransportIcon(
                            option['type']
                                as String,
                          ),
                          color: Colors.blue,
                          size: 28,
                        ),
                      ),

                      const SizedBox(width: 16),

                      Expanded(
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            Text(
                              option['type']
                                  as String,
                              style:
                                  const TextStyle(
                                fontSize: 18,
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),

                            const SizedBox(height: 8),

                            Text(
                              '${formatDateForDisplay(
                                option[
                                    'departure_date']
                                    as String,
                              )} '
                              '${option['departure_time']}',
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              option[
                                      'departure_location']
                                  as String,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),

                            const SizedBox(height: 8),

                            Text(
                              '${formatDateForDisplay(
                                option[
                                    'arrival_date']
                                    as String,
                              )} '
                              '${option['arrival_time']}',
                              style:
                                  const TextStyle(
                                fontSize: 15,
                              ),
                            ),

                            const SizedBox(height: 4),

                            Text(
                              option[
                                      'arrival_location']
                                  as String,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),

                            const SizedBox(height: 8),

                            Text(
                              option['duration']
                                  as String,
                              style: TextStyle(
                                color: Colors
                                    .grey
                                    .shade600,
                              ),
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(width: 8),

                      Text(
                        '€${option['price']}',
                        style:
                            const TextStyle(
                          fontSize: 20,
                          fontWeight:
                              FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}