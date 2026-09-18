import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/transport.dart';
import '../services/transport_service.dart';

class TransportOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const TransportOptionsPage({super.key, required this.trip});

  @override
  State<TransportOptionsPage> createState() => _TransportOptionsPageState();
}

enum TransportSort { price, departureTime, arrivalTime, duration, stops }

class _TransportOptionsPageState extends State<TransportOptionsPage> {
  List<Transport> options = [];

  bool isLoading = true;
  String? errorMessage;

  TransportSort selectedSort = TransportSort.price;
  bool sortAscending = true;

  bool directOnly = false;
  int? maxStops;
  double? maxPrice;

  String? selectedDepartureAirport;
  String? selectedArrivalAirport;

  bool get isReturnTransport => widget.trip['return_transport'] == true;

  @override
  void initState() {
    super.initState();
    loadTransportOptions();
  }

  String formatDateForDisplay(String date) {
    final parts = date.split('-');

    if (parts.length != 3) {
      return date;
    }

    return '${parts[2]}.${parts[1]}.${parts[0]}';
  }

  Future<void> loadTransportOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions = await TransportService.getTransportOptions(
        tripId: tripId,
        isReturnTransport: isReturnTransport,
      );

      if (!mounted) return;

      setState(() {
        options = loadedOptions;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load transport options';
        isLoading = false;
      });
    }
  }

  IconData getTransportIcon(String type) {
    if (type.startsWith('Flight')) {
      return Icons.flight;
    }

    switch (type) {
      case 'Bus':
        return Icons.directions_bus;
      case 'Train':
        return Icons.train;
      default:
        return Icons.directions_transit;
    }
  }

  Future<void> openBookingUrl(String url) async {
    final uri = Uri.parse(url);

    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open booking link.')),
      );
    }
  }

  String getSortLabel(TransportSort sort) {
    switch (sort) {
      case TransportSort.price:
        return 'Price';

      case TransportSort.departureTime:
        return 'Departure time';

      case TransportSort.arrivalTime:
        return 'Arrival time';

      case TransportSort.duration:
        return 'Duration';

      case TransportSort.stops:
        return 'Stops';
    }
  }

  int _timeToMinutes(String time) {
    final parts = time.split(':');

    if (parts.length != 2) {
      return 0;
    }

    final hours = int.tryParse(parts[0]) ?? 0;
    final minutes = int.tryParse(parts[1]) ?? 0;

    return hours * 60 + minutes;
  }

  int _durationToMinutes(String duration) {
    final hourMatch = RegExp(r'(\d+)h').firstMatch(duration);

    final minuteMatch = RegExp(r'(\d+)m').firstMatch(duration);

    final hours = hourMatch != null
        ? int.tryParse(hourMatch.group(1)!) ?? 0
        : 0;

    final minutes = minuteMatch != null
        ? int.tryParse(minuteMatch.group(1)!) ?? 0
        : 0;

    return hours * 60 + minutes;
  }

  String _extractAirportCode(String location) {
    final match = RegExp(r'\(([A-Z0-9]{3})\)').firstMatch(location);

    if (match != null) {
      return match.group(1)!;
    }

    if (location.length == 3 && location == location.toUpperCase()) {
      return location;
    }

    return location;
  }

  List<String> get departureAirports {
    final airports = options
        .where((option) => option.type.startsWith('Flight'))
        .map((option) => _extractAirportCode(option.departureLocation))
        .where((airport) => airport.isNotEmpty)
        .toSet()
        .toList();

    airports.sort();

    return airports;
  }

  List<String> get arrivalAirports {
    final airports = options
        .where((option) => option.type.startsWith('Flight'))
        .map((option) => _extractAirportCode(option.arrivalLocation))
        .where((airport) => airport.isNotEmpty)
        .toSet()
        .toList();

    airports.sort();

    return airports;
  }

  List<Transport> get filteredAndSortedOptions {
    final result = options.where((option) {
      if (directOnly && option.stops != 0) {
        return false;
      }

      if (maxStops != null && option.stops > maxStops!) {
        return false;
      }

      if (maxPrice != null && option.userPrice > maxPrice!) {
        return false;
      }

      if (selectedDepartureAirport != null &&
          option.type.startsWith('Flight')) {
        final airport = _extractAirportCode(option.departureLocation);

        if (airport != selectedDepartureAirport) {
          return false;
        }
      }

      if (selectedArrivalAirport != null && option.type.startsWith('Flight')) {
        final airport = _extractAirportCode(option.arrivalLocation);

        if (airport != selectedArrivalAirport) {
          return false;
        }
      }

      return true;
    }).toList();

    result.sort((a, b) {
      int comparison;

      switch (selectedSort) {
        case TransportSort.price:
          comparison = a.userPrice.compareTo(b.userPrice);
          break;

        case TransportSort.departureTime:
          comparison = _timeToMinutes(a.departureTime)
              .compareTo(_timeToMinutes(b.departureTime));
          break;

        case TransportSort.arrivalTime:
          comparison = _timeToMinutes(a.arrivalTime)
              .compareTo(_timeToMinutes(b.arrivalTime));
          break;

        case TransportSort.duration:
          comparison = _durationToMinutes(a.duration)
              .compareTo(_durationToMinutes(b.duration));
          break;

        case TransportSort.stops:
          comparison = a.stops.compareTo(b.stops);
          break;
      }

      return sortAscending ? comparison : -comparison;
    });

    return result;
  }

  void _resetFilters() {
    setState(() {
      directOnly = false;
      maxStops = null;
      maxPrice = null;
      selectedDepartureAirport = null;
      selectedArrivalAirport = null;
    });
  }

  void _showFilters() {
    bool localDirectOnly = directOnly;
    int? localMaxStops = maxStops;
    double? localMaxPrice = maxPrice;
    String? localDepartureAirport = selectedDepartureAirport;
    String? localArrivalAirport = selectedArrivalAirport;

    final priceController = TextEditingController(
      text: localMaxPrice?.toString() ?? '',
    );

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Filters',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            setSheetState(() {
                              localDirectOnly = false;
                              localMaxStops = null;
                              localMaxPrice = null;
                              localDepartureAirport = null;
                              localArrivalAirport = null;

                              priceController.clear();
                            });
                          },
                          child: const Text('Reset'),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Direct flights only'),
                      value: localDirectOnly,
                      onChanged: (value) {
                        setSheetState(() {
                          localDirectOnly = value;
                        });
                      },
                    ),

                    const SizedBox(height: 12),

                    const Text(
                      'Maximum stops',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),

                    const SizedBox(height: 8),

                    DropdownButtonFormField<int?>(
                      initialValue: localMaxStops,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem<int?>(
                          value: null,
                          child: Text('Any number'),
                        ),
                        DropdownMenuItem<int?>(
                          value: 0,
                          child: Text('Direct only'),
                        ),
                        DropdownMenuItem<int?>(
                          value: 1,
                          child: Text('Up to 1 stop'),
                        ),
                        DropdownMenuItem<int?>(
                          value: 2,
                          child: Text('Up to 2 stops'),
                        ),
                        DropdownMenuItem<int?>(
                          value: 3,
                          child: Text('Up to 3 stops'),
                        ),
                      ],
                      onChanged: (value) {
                        setSheetState(() {
                          localMaxStops = value;
                        });
                      },
                    ),

                    const SizedBox(height: 18),

                    const Text(
                      'Maximum price',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),

                    const SizedBox(height: 8),

                    TextField(
                      controller: priceController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: InputDecoration(
                        hintText:
                            'Maximum price in '
                            '${options.isNotEmpty ? options.first.userCurrency : ''}',
                        border: const OutlineInputBorder(),
                      ),
                      onChanged: (value) {
                        localMaxPrice = double.tryParse(
                          value.replaceAll(',', '.'),
                        );
                      },
                    ),

                    if (departureAirports.isNotEmpty) ...[
                      const SizedBox(height: 18),

                      const Text(
                        'Departure airport',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 8),

                      DropdownButtonFormField<String?>(
                        initialValue: localDepartureAirport,
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          const DropdownMenuItem<String?>(
                            value: null,
                            child: Text('Any airport'),
                          ),
                          ...departureAirports.map(
                            (airport) => DropdownMenuItem<String?>(
                              value: airport,
                              child: Text(airport),
                            ),
                          ),
                        ],
                        onChanged: (value) {
                          setSheetState(() {
                            localDepartureAirport = value;
                          });
                        },
                      ),
                    ],

                    if (arrivalAirports.isNotEmpty) ...[
                      const SizedBox(height: 18),

                      const Text(
                        'Arrival airport',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 8),

                      DropdownButtonFormField<String?>(
                        initialValue: localArrivalAirport,
                        decoration: const InputDecoration(
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          const DropdownMenuItem<String?>(
                            value: null,
                            child: Text('Any airport'),
                          ),
                          ...arrivalAirports.map(
                            (airport) => DropdownMenuItem<String?>(
                              value: airport,
                              child: Text(airport),
                            ),
                          ),
                        ],
                        onChanged: (value) {
                          setSheetState(() {
                            localArrivalAirport = value;
                          });
                        },
                      ),
                    ],

                    const SizedBox(height: 24),

                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: () {
                          setState(() {
                            directOnly = localDirectOnly;
                            maxStops = localMaxStops;
                            maxPrice = localMaxPrice;
                            selectedDepartureAirport = localDepartureAirport;
                            selectedArrivalAirport = localArrivalAirport;
                          });

                          Navigator.pop(sheetContext);
                        },
                        child: const Text('Apply filters'),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    ).whenComplete(() {
      priceController.dispose();
    });
  }

  void _showSortOptions() {
    showModalBottomSheet(
      context: context,
      builder: (sheetContext) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Padding(
                padding: EdgeInsets.all(20),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Sort by',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                ),
              ),

              ...TransportSort.values.map((sort) {
                final selected = selectedSort == sort;

                return ListTile(
                  title: Text(getSortLabel(sort)),
                  trailing: selected
                      ? const Icon(Icons.check, color: Colors.blue)
                      : null,
                  onTap: () {
                    setState(() {
                      selectedSort = sort;
                    });

                    Navigator.pop(sheetContext);
                  },
                );
              }),

              const Divider(),

              ListTile(
                title: const Text('Ascending'),
                leading: Radio<bool>(
                  value: true,
                  groupValue: sortAscending,
                  onChanged: (value) {
                    setState(() {
                      sortAscending = true;
                    });

                    Navigator.pop(sheetContext);
                  },
                ),
                onTap: () {
                  setState(() {
                    sortAscending = true;
                  });

                  Navigator.pop(sheetContext);
                },
              ),

              ListTile(
                title: const Text('Descending'),
                leading: Radio<bool>(
                  value: false,
                  groupValue: sortAscending,
                  onChanged: (value) {
                    setState(() {
                      sortAscending = false;
                    });

                    Navigator.pop(sheetContext);
                  },
                ),
                onTap: () {
                  setState(() {
                    sortAscending = false;
                  });

                  Navigator.pop(sheetContext);
                },
              ),

              const SizedBox(height: 10),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final origin = widget.trip['origin'];
    final destination = widget.trip['destination'];

    final from = isReturnTransport ? destination : origin;

    final to = isReturnTransport ? origin : destination;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          isReturnTransport ? 'Return Transport' : 'Transport Options',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: _buildBody(from, to),
    );
  }

  Widget _buildBody(String from, String to) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            errorMessage!,
            style: const TextStyle(fontSize: 16),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    final displayedOptions = filteredAndSortedOptions;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$from → $to',
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          Text(
            isReturnTransport
                ? 'Choose how you want to get back'
                : 'Choose how you want to get there',
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),

          const SizedBox(height: 20),

          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _showSortOptions,
                  icon: const Icon(Icons.sort),
                  label: Text(getSortLabel(selectedSort)),
                ),
              ),

              const SizedBox(width: 10),

              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _showFilters,
                  icon: const Icon(Icons.tune),
                  label: const Text('Filters'),
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${displayedOptions.length} '
                '${displayedOptions.length == 1 ? 'option' : 'options'}',
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),

              if (directOnly ||
                  maxStops != null ||
                  maxPrice != null ||
                  selectedDepartureAirport != null ||
                  selectedArrivalAirport != null)
                TextButton(
                  onPressed: _resetFilters,
                  child: const Text('Clear filters'),
                ),
            ],
          ),

          const SizedBox(height: 12),

          if (options.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 40),
              child: Center(
                child: Text(
                  'No transport tickets were found for this route.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                ),
              ),
            )
          else if (displayedOptions.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 40),
              child: Center(
                child: Text(
                  'No transport options match the selected filters.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                ),
              ),
            ),

          ...displayedOptions.map((option) => _buildTransportCard(option)),
        ],
      ),
    );
  }

  Widget _buildTransportCard(Transport option) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.pop(context, option);
        },
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
                  getTransportIcon(option.type),
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
                      option.type,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),

                    if (option.type.startsWith('Flight')) ...[
                      const SizedBox(height: 4),
                      Text(
                        option.stops == 0
                            ? 'Direct'
                            : '${option.stops} '
                                  '${option.stops == 1 ? 'stop' : 'stops'}',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],

                    const SizedBox(height: 8),

                    Text(
                      '${formatDateForDisplay(option.departureDate)} '
                      '${option.departureTime}',
                      style: const TextStyle(fontSize: 15),
                    ),

                    const SizedBox(height: 4),

                    Text(
                      option.departureLocation,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      '${formatDateForDisplay(option.arrivalDate)} '
                      '${option.arrivalTime}',
                      style: const TextStyle(fontSize: 15),
                    ),

                    const SizedBox(height: 4),

                    Text(
                      option.arrivalLocation,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      option.duration,
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),

              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${option.userPrice.toStringAsFixed(2)} '
                    '${option.userCurrency}',
                    textAlign: TextAlign.right,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),

                  const SizedBox(height: 4),

                  Text(
                    '${option.destinationPrice.toStringAsFixed(2)} '
                    '${option.destinationCurrency}',
                    textAlign: TextAlign.right,
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                  ),

                  const SizedBox(height: 4),

                  Text(
                    '${option.price.toStringAsFixed(2)} '
                    '${option.currency}',
                    textAlign: TextAlign.right,
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                  ),

                  if (option.bookingUrl != null &&
                      option.bookingUrl!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: () {
                        openBookingUrl(option.bookingUrl!);
                      },
                      child: const Text('Buy ticket'),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
