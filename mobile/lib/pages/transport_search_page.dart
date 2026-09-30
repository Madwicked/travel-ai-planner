import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/transport.dart';
import '../services/api_service.dart';
import '../services/transport_service.dart';

class TransportSearchPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final String? transportType;

  const TransportSearchPage({
    super.key,
    required this.trip,
    this.transportType,
  });

  @override
  State<TransportSearchPage> createState() => _TransportSearchPage();
}

enum TransportSort { price, departureTime, arrivalTime, duration, stops }

class _TransportSearchPage extends State<TransportSearchPage> {
  List<Transport> options = [];

  bool isLoading = true;
  String? errorMessage;
  String? searchDate;

  TransportSort selectedSort = TransportSort.price;
  bool sortAscending = true;

  bool directOnly = false;
  int? maxStops;
  double? maxPrice;

  String? selectedDepartureAirport;
  String? selectedArrivalAirport;

  int? maxDurationMinutes;

  final Set<String> departureTimeRanges = {};

  final ScrollController _scrollController = ScrollController();
  bool _showScrollToTop = false;

  int currentOffset = 0;
  int pageSize = 50;

  bool isLoadingMore = false;

  bool get hasMore => currentOffset < filteredAndSortedOptions.length;

  bool get isReturnTransport => widget.trip['return_transport'] == true;

  @override
  void initState() {
    super.initState();

    _scrollController.addListener(_handleScroll);

    searchDate = isReturnTransport
        ? widget.trip['end_date']
        : widget.trip['start_date'];

    loadTransportOptions();
  }

  @override
  void dispose() {
    _scrollController.removeListener(_handleScroll);
    _scrollController.dispose();

    super.dispose();
  }

  void _handleScroll() {
    final shouldShow = _scrollController.offset > 500;

    if (shouldShow != _showScrollToTop && mounted) {
      setState(() {
        _showScrollToTop = shouldShow;
      });
    }
  }

  void _scrollToTop() {
    _scrollController.animateTo(
      0,
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeOut,
    );
  }

  String formatDateForDisplay(String date) {
    final parts = date.split('-');

    if (parts.length != 3) {
      return date;
    }

    return '${parts[2]}.${parts[1]}.${parts[0]}';
  }

  bool _matchesTransportType(Transport option) {
    if (widget.transportType == null) {
      return true;
    }

    if (widget.transportType == 'Flight') {
      return option.type.startsWith('Flight');
    }

    return option.type == widget.transportType;
  }

  Future<void> loadTransportOptions() async {
    final tripId = widget.trip['id'];

    if (!mounted) return;

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final loadedOptions = await TransportService.getTransportOptions(
        tripId: tripId,
        isReturnTransport: isReturnTransport,
        searchDate: searchDate,
      );

      final filteredOptions = loadedOptions
          .where(_matchesTransportType)
          .toList();

      if (!mounted) return;

      setState(() {
        options = filteredOptions;

        currentOffset = filteredOptions.length > pageSize
            ? pageSize
            : filteredOptions.length;

        isLoading = false;
        isLoadingMore = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load transport options';
        isLoading = false;
        isLoadingMore = false;
      });
    }
  }

  void loadMoreTransportOptions() {
    if (isLoadingMore || !hasMore) return;

    setState(() {
      isLoadingMore = true;

      currentOffset = (currentOffset + pageSize).clamp(
        0,
        filteredAndSortedOptions.length,
      );

      isLoadingMore = false;
    });
  }

  Future<void> _changeSearchDate() async {
    final currentDate = DateTime.parse(searchDate!);

    final selectedDate = await showDatePicker(
      context: context,
      initialDate: currentDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
    );

    if (selectedDate == null) {
      return;
    }

    final newSearchDate =
        '${selectedDate.year.toString().padLeft(4, '0')}-'
        '${selectedDate.month.toString().padLeft(2, '0')}-'
        '${selectedDate.day.toString().padLeft(2, '0')}';

    final tripStartDate = DateTime.parse(widget.trip['start_date']);
    final tripEndDate = DateTime.parse(widget.trip['end_date']);

    String newStartDate = widget.trip['start_date'];
    String newEndDate = widget.trip['end_date'];

    if (isReturnTransport) {
      if (!selectedDate.isAfter(tripStartDate)) {
        if (!mounted) return;

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Return date must be after the departure date.'),
          ),
        );

        return;
      }

      newEndDate = newSearchDate;
    } else {
      final tripDuration = tripEndDate.difference(tripStartDate);

      newStartDate = newSearchDate;

      if (!selectedDate.isBefore(tripEndDate)) {
        final newEnd = selectedDate.add(tripDuration);

        newEndDate =
            '${newEnd.year.toString().padLeft(4, '0')}-'
            '${newEnd.month.toString().padLeft(2, '0')}-'
            '${newEnd.day.toString().padLeft(2, '0')}';
      }
    }

    setState(() {
      searchDate = newSearchDate;
      options = [];
      currentOffset = 0;
      isLoading = true;
      errorMessage = null;
    });

    try {
      final loadedOptions = await TransportService.getTransportOptions(
        tripId: widget.trip['id'],
        isReturnTransport: isReturnTransport,
        searchDate: newSearchDate,
      );

      final filteredOptions = loadedOptions
          .where(_matchesTransportType)
          .toList();

      if (!mounted) return;

      if (filteredOptions.isEmpty) {
        setState(() {
          options = [];
          currentOffset = 0;
          isLoading = false;
        });

        return;
      }

      await ApiService.updateTripDates(
        tripId: widget.trip['id'],
        startDate: newStartDate,
        endDate: newEndDate,
      );

      widget.trip['start_date'] = newStartDate;
      widget.trip['end_date'] = newEndDate;

      setState(() {
        options = filteredOptions;

        currentOffset = filteredOptions.length > pageSize
            ? pageSize
            : filteredOptions.length;

        isLoading = false;
        isLoadingMore = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        options = [];
        currentOffset = 0;
        isLoading = false;
        errorMessage = 'Failed to load transport options';
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

  bool _matchesDepartureTimeFilter(Transport option) {
    if (departureTimeRanges.isEmpty) {
      return true;
    }

    if (departureTimeRanges.length == 4) {
      return true;
    }

    final departureMinutes = _timeToMinutes(option.departureTime);

    if (departureMinutes >= 0 && departureMinutes < 360) {
      return departureTimeRanges.contains('00:00-06:00');
    }

    if (departureMinutes >= 360 && departureMinutes < 720) {
      return departureTimeRanges.contains('06:00-12:00');
    }

    if (departureMinutes >= 720 && departureMinutes < 1080) {
      return departureTimeRanges.contains('12:00-18:00');
    }

    return departureTimeRanges.contains('18:00-24:00');
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

      if (!_matchesDepartureTimeFilter(option)) {
        return false;
      }

      if (maxDurationMinutes != null) {
        final durationMinutes = _durationToMinutes(option.duration);

        if (durationMinutes > maxDurationMinutes!) {
          return false;
        }
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

  List<Transport> get visibleOptions {
    final end = currentOffset.clamp(0, filteredAndSortedOptions.length);

    return filteredAndSortedOptions.take(end).toList();
  }

  void _resetFilters() {
    setState(() {
      directOnly = false;
      maxStops = null;
      maxPrice = null;
      maxDurationMinutes = null;

      selectedDepartureAirport = null;
      selectedArrivalAirport = null;

      departureTimeRanges.clear();

      currentOffset = filteredAndSortedOptions.length > pageSize
          ? pageSize
          : filteredAndSortedOptions.length;
    });
  }

  InputDecoration _filterDecoration({String? labelText}) {
    return InputDecoration(
      labelText: labelText,
      isDense: true,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
    );
  }

  Widget _timeFilterChip({
    required String label,
    required String value,
    required Set<String> selectedRanges,
    required StateSetter setSheetState,
  }) {
    final selected = selectedRanges.contains(value);

    return FilterChip(
      label: Text(label),
      selected: selected,
      showCheckmark: true,
      visualDensity: VisualDensity.compact,
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      onSelected: (valueSelected) {
        setSheetState(() {
          if (valueSelected) {
            selectedRanges.add(value);
          } else {
            selectedRanges.remove(value);
          }
        });
      },
    );
  }

  void _showFilters() {
    bool localDirectOnly = directOnly;
    int? localMaxStops = maxStops;
    double? localMaxPrice = maxPrice;
    int? localMaxDurationMinutes = maxDurationMinutes;

    String? localDepartureAirport = selectedDepartureAirport;
    String? localArrivalAirport = selectedArrivalAirport;

    final Set<String> localDepartureTimeRanges = Set<String>.from(
      departureTimeRanges,
    );

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            final allTimeRangesSelected = localDepartureTimeRanges.length == 4;

            return SafeArea(
              child: Padding(
                padding: EdgeInsets.only(
                  left: 20,
                  right: 20,
                  top: 16,
                  bottom: MediaQuery.of(context).viewInsets.bottom + 16,
                ),
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
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
                                localMaxDurationMinutes = null;

                                localDepartureAirport = null;
                                localArrivalAirport = null;

                                localDepartureTimeRanges.clear();
                              });
                            },
                            child: const Text('Reset'),
                          ),
                        ],
                      ),

                      const SizedBox(height: 8),

                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        title: const Text('Direct flights only'),
                        value: localDirectOnly,
                        onChanged: (value) {
                          setSheetState(() {
                            localDirectOnly = value;

                            if (value) {
                              localMaxStops = 0;
                            }
                          });
                        },
                      ),

                      const SizedBox(height: 8),

                      const Text(
                        'Maximum stops',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 6),

                      DropdownButtonFormField<int?>(
                        initialValue: localMaxStops,
                        decoration: _filterDecoration(),
                        items: const [
                          DropdownMenuItem<int?>(
                            value: null,
                            child: Text('Any number'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 0,
                            child: Text('Direct'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 1,
                            child: Text('Up to 1 stop'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 2,
                            child: Text('Up to 2 stops'),
                          ),
                        ],
                        onChanged: (value) {
                          setSheetState(() {
                            localMaxStops = value;

                            if (value != null && value > 0) {
                              localDirectOnly = false;
                            }
                          });
                        },
                      ),

                      const SizedBox(height: 12),

                      const Text(
                        'Maximum price',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 6),

                      DropdownButtonFormField<double?>(
                        initialValue: localMaxPrice,
                        decoration: _filterDecoration(),
                        items: const [
                          DropdownMenuItem<double?>(
                            value: null,
                            child: Text('Any price'),
                          ),
                          DropdownMenuItem<double?>(
                            value: 100,
                            child: Text('Up to €100'),
                          ),
                          DropdownMenuItem<double?>(
                            value: 200,
                            child: Text('Up to €200'),
                          ),
                          DropdownMenuItem<double?>(
                            value: 300,
                            child: Text('Up to €300'),
                          ),
                          DropdownMenuItem<double?>(
                            value: 500,
                            child: Text('Up to €500'),
                          ),
                          DropdownMenuItem<double?>(
                            value: 1000,
                            child: Text('Up to €1000'),
                          ),
                        ],
                        onChanged: (value) {
                          setSheetState(() {
                            localMaxPrice = value;
                          });
                        },
                      ),

                      const SizedBox(height: 12),

                      const Text(
                        'Maximum flight duration',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 6),

                      DropdownButtonFormField<int?>(
                        initialValue: localMaxDurationMinutes,
                        decoration: _filterDecoration(),
                        items: const [
                          DropdownMenuItem<int?>(
                            value: null,
                            child: Text('Any duration'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 180,
                            child: Text('Up to 3 hours'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 300,
                            child: Text('Up to 5 hours'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 360,
                            child: Text('Up to 6 hours'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 480,
                            child: Text('Up to 8 hours'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 600,
                            child: Text('Up to 10 hours'),
                          ),
                          DropdownMenuItem<int?>(
                            value: 720,
                            child: Text('Up to 12 hours'),
                          ),
                        ],
                        onChanged: (value) {
                          setSheetState(() {
                            localMaxDurationMinutes = value;
                          });
                        },
                      ),

                      const SizedBox(height: 12),

                      const Text(
                        'Departure time',
                        style: TextStyle(fontWeight: FontWeight.w600),
                      ),

                      const SizedBox(height: 6),

                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: [
                          _timeFilterChip(
                            label: '00–06',
                            value: '00:00-06:00',
                            selectedRanges: localDepartureTimeRanges,
                            setSheetState: setSheetState,
                          ),
                          _timeFilterChip(
                            label: '06–12',
                            value: '06:00-12:00',
                            selectedRanges: localDepartureTimeRanges,
                            setSheetState: setSheetState,
                          ),
                          _timeFilterChip(
                            label: '12–18',
                            value: '12:00-18:00',
                            selectedRanges: localDepartureTimeRanges,
                            setSheetState: setSheetState,
                          ),
                          _timeFilterChip(
                            label: '18–24',
                            value: '18:00-24:00',
                            selectedRanges: localDepartureTimeRanges,
                            setSheetState: setSheetState,
                          ),
                        ],
                      ),

                      if (allTimeRangesSelected)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(
                            'All departure times selected',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ),

                      if (departureAirports.isNotEmpty ||
                          arrivalAirports.isNotEmpty) ...[
                        const SizedBox(height: 12),

                        const Text(
                          'Airports',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),

                        const SizedBox(height: 6),

                        if (departureAirports.isNotEmpty)
                          DropdownButtonFormField<String?>(
                            initialValue: localDepartureAirport,
                            decoration: _filterDecoration(
                              labelText: 'Departure',
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

                        if (departureAirports.isNotEmpty &&
                            arrivalAirports.isNotEmpty)
                          const SizedBox(height: 8),

                        if (arrivalAirports.isNotEmpty)
                          DropdownButtonFormField<String?>(
                            initialValue: localArrivalAirport,
                            decoration: _filterDecoration(labelText: 'Arrival'),
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

                      const SizedBox(height: 18),

                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: () {
                            setState(() {
                              directOnly = localDirectOnly;
                              maxStops = localMaxStops;
                              maxPrice = localMaxPrice;
                              maxDurationMinutes = localMaxDurationMinutes;

                              selectedDepartureAirport = localDepartureAirport;
                              selectedArrivalAirport = localArrivalAirport;

                              departureTimeRanges
                                ..clear()
                                ..addAll(localDepartureTimeRanges);

                              final filteredCount =
                                  filteredAndSortedOptions.length;

                              currentOffset = filteredCount > pageSize
                                  ? pageSize
                                  : filteredCount;
                            });

                            Navigator.of(context).pop();
                          },
                          child: const Text('Apply filters'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
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

                      final filteredCount = filteredAndSortedOptions.length;

                      currentOffset = filteredCount > pageSize
                          ? pageSize
                          : filteredCount;
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

                      final filteredCount = filteredAndSortedOptions.length;

                      currentOffset = filteredCount > pageSize
                          ? pageSize
                          : filteredCount;
                    });

                    Navigator.pop(sheetContext);
                  },
                ),
                onTap: () {
                  setState(() {
                    sortAscending = true;

                    final filteredCount = filteredAndSortedOptions.length;

                    currentOffset = filteredCount > pageSize
                        ? pageSize
                        : filteredCount;
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

                      final filteredCount = filteredAndSortedOptions.length;

                      currentOffset = filteredCount > pageSize
                          ? pageSize
                          : filteredCount;
                    });

                    Navigator.pop(sheetContext);
                  },
                ),
                onTap: () {
                  setState(() {
                    sortAscending = false;

                    final filteredCount = filteredAndSortedOptions.length;

                    currentOffset = filteredCount > pageSize
                        ? pageSize
                        : filteredCount;
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
          widget.transportType != null
              ? '${widget.transportType} Tickets'
              : isReturnTransport
              ? 'Return Transport'
              : 'Transport Options',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      floatingActionButton: _showScrollToTop
          ? FloatingActionButton(
              onPressed: _scrollToTop,
              child: const Icon(Icons.keyboard_arrow_up),
            )
          : null,
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

    final filteredOptions = filteredAndSortedOptions;
    final displayedOptions = visibleOptions;

    final hasActiveFilters =
        directOnly ||
        maxStops != null ||
        maxPrice != null ||
        maxDurationMinutes != null ||
        selectedDepartureAirport != null ||
        selectedArrivalAirport != null ||
        departureTimeRanges.isNotEmpty;

    return SingleChildScrollView(
      controller: _scrollController,
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
                hasActiveFilters
                    ? '${filteredOptions.length} of ${options.length} tickets found'
                    : '${filteredOptions.length} tickets found',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey.shade600,
                  fontWeight: FontWeight.w500,
                ),
              ),

              if (hasActiveFilters)
                TextButton(
                  onPressed: _resetFilters,
                  child: const Text('Clear filters'),
                ),
            ],
          ),

          const SizedBox(height: 12),

          if (options.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 40),
              child: Center(
                child: Column(
                  children: [
                    Text(
                      widget.transportType != null
                          ? 'No ${widget.transportType!.toLowerCase()} tickets were found for the selected date.'
                          : 'No transport tickets were found for the selected date.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),

                    const SizedBox(height: 16),

                    OutlinedButton.icon(
                      onPressed: _changeSearchDate,
                      icon: const Icon(Icons.calendar_month),
                      label: const Text('Change date'),
                    ),
                  ],
                ),
              ),
            )
          else if (filteredOptions.isEmpty)
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

          if (hasMore && displayedOptions.isNotEmpty) ...[
            const SizedBox(height: 16),
            Center(
              child: isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: CircularProgressIndicator(),
                    )
                  : ElevatedButton(
                      onPressed: loadMoreTransportOptions,
                      child: const Text('View more'),
                    ),
            ),
          ],

          const SizedBox(height: 80),
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
