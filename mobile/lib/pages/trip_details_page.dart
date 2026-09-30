import 'package:flutter/material.dart';

import 'hotel_details_page.dart';
import 'hotel_options_page.dart';
import 'itinerary_page.dart';
import 'place_options_page.dart';
import 'transport_details_page.dart';
import 'transport_type_selection_page.dart';
import '../models/hotel.dart';
import '../models/place.dart';
import '../models/transport.dart';
import '../services/api_service.dart';
import '../services/hotel_service.dart';
import '../services/place_service.dart';
import '../services/transport_service.dart';
import 'transfer_selection_page.dart';
import '../models/trip_stop.dart';
import '../services/trip_stop_service.dart';
import '../models/location.dart';
import '../widgets/trip_dialogs.dart';

class TripDetailsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const TripDetailsPage({super.key, required this.trip});

  @override
  State<TripDetailsPage> createState() => _TripDetailsPageState();
}

class _TripDetailsPageState extends State<TripDetailsPage> {
  List<Transport> selectedOutboundTransports = [];
  List<Transport> selectedReturnTransports = [];

  String? outboundTransferChoice;
  String? returnTransferChoice;

  // Temporary legacy state.
  // It is still used by transfer selection and TransportDetailsPage.
  Hotel? selectedHotel;

  Map<int, Hotel> selectedStopHotels = {};

  List<Place> selectedPlaces = [];

  List<TripStop> tripStops = [];
  bool isLoadingTripStops = true;

  String foodPreference = 'Mixed';

  String _formatDate(String date) {
    final parsedDate = DateTime.tryParse(date);

    if (parsedDate == null) return date;

    final day = parsedDate.day.toString().padLeft(2, '0');
    final month = parsedDate.month.toString().padLeft(2, '0');

    return '$day.$month.${parsedDate.year}';
  }

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

  bool includeArrivalDayActivities = false;
  bool includeDepartureDayActivities = false;

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
    loadTripStops();
    loadBudget();
  }

  Future<void> addTripStop() async {
    Location? selectedCity;

    DateTime? startDate;
    DateTime? endDate;

    bool citySelected = false;

    final tripStartDate = DateTime.parse(widget.trip['start_date'].toString());

    final tripEndDate = DateTime.parse(widget.trip['end_date'].toString());

    final tripCountry = widget.trip['destination_country']
        ?.toString()
        .trim()
        .toLowerCase();

    final cityController = TextEditingController();

    bool isStartDateAvailable(DateTime date) {
      if (!date.isBefore(tripEndDate)) {
        return false;
      }

      for (final stop in tripStops) {
        final stopStart = DateTime(
          stop.startDate.year,
          stop.startDate.month,
          stop.startDate.day,
        );

        final stopEnd = DateTime(
          stop.endDate.year,
          stop.endDate.month,
          stop.endDate.day,
        );

        if (!date.isBefore(stopStart) && date.isBefore(stopEnd)) {
          return false;
        }
      }

      return true;
    }

    bool isEndDateAvailable(DateTime date) {
      if (startDate == null || !date.isAfter(startDate!)) {
        return false;
      }

      for (final stop in tripStops) {
        final stopStart = DateTime(
          stop.startDate.year,
          stop.startDate.month,
          stop.startDate.day,
        );

        final stopEnd = DateTime(
          stop.endDate.year,
          stop.endDate.month,
          stop.endDate.day,
        );

        if (date.isAfter(stopStart) && !date.isAfter(stopEnd)) {
          return false;
        }
      }

      return true;
    }

    DateTime findAvailableDate(
      DateTime initialDate,
      DateTime minimumDate,
      DateTime maximumDate,
      bool isStartDate,
    ) {
      var date = initialDate;

      if (date.isBefore(minimumDate)) {
        date = minimumDate;
      }

      if (date.isAfter(maximumDate)) {
        date = maximumDate;
      }

      while (date.isBefore(maximumDate) || date.isAtSameMomentAs(maximumDate)) {
        final available = isStartDate
            ? isStartDateAvailable(date)
            : isEndDateAvailable(date);

        if (available) {
          return date;
        }

        date = date.add(const Duration(days: 1));
      }

      return minimumDate;
    }

    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            Future<void> selectStopDate(bool isStartDate) async {
              final minimumDate = isStartDate
                  ? tripStartDate
                  : startDate!.add(const Duration(days: 1));

              final maximumDate = tripEndDate;

              if (minimumDate.isAfter(maximumDate)) {
                return;
              }

              final initialDate = isStartDate
                  ? (startDate ?? tripStartDate)
                  : (endDate ?? minimumDate);

              final safeInitialDate = findAvailableDate(
                initialDate,
                minimumDate,
                maximumDate,
                isStartDate,
              );

              DateTime? calendarInitialDate;

              final isDateAvailable = (DateTime date) {
                return isStartDate
                    ? isStartDateAvailable(date)
                    : isEndDateAvailable(date);
              };

              // Сначала пытаемся использовать текущую дату.
              if (!safeInitialDate.isBefore(minimumDate) &&
                  !safeInitialDate.isAfter(maximumDate) &&
                  isDateAvailable(safeInitialDate)) {
                calendarInitialDate = safeInitialDate;
              } else {
                // Ищем ближайшую доступную дату вперёд.
                DateTime candidate = safeInitialDate.isBefore(minimumDate)
                    ? minimumDate
                    : safeInitialDate;

                while (!candidate.isAfter(maximumDate)) {
                  if (isDateAvailable(candidate)) {
                    calendarInitialDate = candidate;
                    break;
                  }

                  candidate = candidate.add(const Duration(days: 1));
                }
              }

              // Если в разрешённом диапазоне вообще нет доступных дат,
              // календарь открывать нельзя.
              if (calendarInitialDate == null) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        isStartDate
                            ? 'Нет доступных дат для начала остановки.'
                            : 'Нет доступных дат для окончания остановки.',
                      ),
                    ),
                  );
                }

                return;
              }

              final selected = await showDialog<DateTime>(
                context: context,
                builder: (calendarContext) {
                  return Dialog(
                    child: CalendarDatePicker(
                      initialDate: calendarInitialDate!,
                      firstDate: minimumDate,
                      lastDate: maximumDate,
                      selectableDayPredicate: isDateAvailable,
                      onDateChanged: (date) {
                        Navigator.of(calendarContext).pop(date);
                      },
                    ),
                  );
                },
              );

              if (selected == null) {
                return;
              }

              setDialogState(() {
                if (isStartDate) {
                  startDate = selected;

                  if (endDate != null && !endDate!.isAfter(selected)) {
                    endDate = null;
                  }
                } else {
                  endDate = selected;
                }
              });
            }

            String formatStopDate(DateTime? date) {
              if (date == null) {
                return 'Select date';
              }

              return '${date.day.toString().padLeft(2, '0')}.'
                  '${date.month.toString().padLeft(2, '0')}.'
                  '${date.year}';
            }

            return AlertDialog(
              title: const Text('Add city'),
              content: SizedBox(
                width: 500,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'City',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      RawAutocomplete<Location>(
                        optionsBuilder:
                            (TextEditingValue textEditingValue) async {
                              final query = textEditingValue.text.trim();

                              if (query.length < 2 || citySelected) {
                                return const Iterable<Location>.empty();
                              }

                              final cities = await ApiService.searchCities(
                                query,
                              );

                              final locations = cities
                                  .map((city) => Location.fromJson(city))
                                  .toList();

                              if (tripCountry == null || tripCountry.isEmpty) {
                                return locations;
                              }

                              locations.sort((a, b) {
                                final aIsTripCountry =
                                    a.country.trim().toLowerCase() ==
                                    tripCountry;

                                final bIsTripCountry =
                                    b.country.trim().toLowerCase() ==
                                    tripCountry;

                                if (aIsTripCountry && !bIsTripCountry) {
                                  return -1;
                                }

                                if (!aIsTripCountry && bIsTripCountry) {
                                  return 1;
                                }

                                return 0;
                              });

                              return locations;
                            },
                        displayStringForOption: (city) {
                          return city.displayName;
                        },
                        onSelected: (city) {
                          selectedCity = city;
                          citySelected = true;

                          cityController.text = city.displayName;

                          setDialogState(() {});
                        },
                        fieldViewBuilder:
                            (context, controller, focusNode, onFieldSubmitted) {
                              return TextField(
                                controller: controller,
                                focusNode: focusNode,
                                onChanged: (value) {
                                  cityController.text = value;

                                  if (citySelected &&
                                      value != selectedCity?.displayName) {
                                    citySelected = false;
                                    selectedCity = null;
                                  }

                                  setDialogState(() {});
                                },
                                decoration: InputDecoration(
                                  hintText: 'e.g. Belgrade, Serbia',
                                  prefixIcon: const Icon(
                                    Icons.location_on_outlined,
                                  ),
                                  suffixIcon: controller.text.isNotEmpty
                                      ? IconButton(
                                          icon: const Icon(Icons.clear),
                                          onPressed: () {
                                            controller.clear();
                                            cityController.clear();

                                            selectedCity = null;
                                            citySelected = false;

                                            setDialogState(() {});
                                          },
                                        )
                                      : null,
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(14),
                                  ),
                                ),
                              );
                            },
                        optionsViewBuilder: (context, onSelected, options) {
                          if (citySelected) {
                            return const SizedBox.shrink();
                          }

                          return Align(
                            alignment: Alignment.topLeft,
                            child: Material(
                              elevation: 4,
                              child: ListView.builder(
                                padding: EdgeInsets.zero,
                                shrinkWrap: true,
                                itemCount: options.length,
                                itemBuilder: (context, index) {
                                  final city = options.elementAt(index);

                                  return ListTile(
                                    title: Text(city.name),
                                    subtitle: Text(city.country),
                                    onTap: () {
                                      onSelected(city);
                                    },
                                  );
                                },
                              ),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 20),
                      const Text(
                        'Stay dates',
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
                              onPressed: () {
                                selectStopDate(true);
                              },
                              icon: const Icon(Icons.calendar_today),
                              label: Text(formatStopDate(startDate)),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: startDate == null
                                  ? null
                                  : () {
                                      selectStopDate(false);
                                    },
                              icon: const Icon(Icons.calendar_today),
                              label: Text(formatStopDate(endDate)),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Trip dates: '
                        '${tripStartDate.day.toString().padLeft(2, '0')}.'
                        '${tripStartDate.month.toString().padLeft(2, '0')}.'
                        '${tripStartDate.year}'
                        ' — '
                        '${tripEndDate.day.toString().padLeft(2, '0')}.'
                        '${tripEndDate.month.toString().padLeft(2, '0')}.'
                        '${tripEndDate.year}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.of(dialogContext).pop(false);
                  },
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed:
                      selectedCity == null ||
                          startDate == null ||
                          endDate == null
                      ? null
                      : () {
                          Navigator.of(dialogContext).pop(true);
                        },
                  child: const Text('Add'),
                ),
              ],
            );
          },
        );
      },
    );

    if (result != true ||
        selectedCity == null ||
        startDate == null ||
        endDate == null) {
      cityController.dispose();
      return;
    }

    try {
      await TripStopService.createTripStop(
        tripId: widget.trip['id'],
        city: selectedCity!.name,
        country: selectedCity!.country,
        latitude: selectedCity!.latitude,
        longitude: selectedCity!.longitude,
        startDate: startDate!,
        endDate: endDate!,
      );

      await loadTripStops();

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${selectedCity!.name} added to trip.')),
      );
    } catch (e) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to add city: $e')));
    } finally {
      cityController.dispose();
    }
  }

  Hotel? _getHotelForTransport(Transport transport) {
    print(
      'FIND HOTEL FOR TRANSPORT: '
      'direction=${transport.direction}, '
      'arrival=${transport.arrivalDate}, '
      'departure=${transport.departureDate}, '
      'tripStops=${tripStops.length}, '
      'selectedStopHotels=${selectedStopHotels.keys.toList()}',
    );

    if (tripStops.isEmpty) {
      return selectedHotel;
    }

    final bool isReturn = transport.direction == 'return';

    final String dateString = isReturn
        ? transport.departureDate
        : transport.arrivalDate;

    final DateTime? transportDate = DateTime.tryParse(dateString);

    if (transportDate == null) {
      return null;
    }

    if (isReturn) {
      // Return transfer: hotel -> departure airport.
      // Find the stop in which the departure date belongs.
      for (final stop in tripStops) {
        final hotel = selectedStopHotels[stop.id];

        if (hotel == null) {
          continue;
        }

        final bool matchesDate =
            !transportDate.isBefore(stop.startDate) &&
            !transportDate.isAfter(stop.endDate);

        if (!matchesDate) {
          continue;
        }

        print(
          'HOTEL FOR RETURN TRANSFER: '
          'date=$transportDate, '
          'stop=${stop.city}, '
          'hotel=${hotel.name}, '
          'hotelId=${hotel.id}',
        );

        return hotel;
      }
    } else {
      // Outbound transfer: arrival airport -> hotel.
      //
      // The hotel can start on the next day, so first find
      // the first selected hotel whose stop starts on or after
      // the arrival date.
      final matchingStops =
          tripStops
              .where(
                (stop) =>
                    !stop.startDate.isBefore(transportDate) &&
                    selectedStopHotels.containsKey(stop.id),
              )
              .toList()
            ..sort((a, b) => a.startDate.compareTo(b.startDate));

      if (matchingStops.isNotEmpty) {
        final stop = matchingStops.first;
        final hotel = selectedStopHotels[stop.id];

        print(
          'HOTEL FOR OUTBOUND TRANSFER: '
          'arrivalDate=$transportDate, '
          'stop=${stop.city}, '
          'hotel=${hotel?.name}, '
          'hotelId=${hotel?.id}',
        );

        return hotel;
      }

      // Fallback: if the arrival date is already inside a stop,
      // use that stop's hotel.
      for (final stop in tripStops) {
        final hotel = selectedStopHotels[stop.id];

        if (hotel == null) {
          continue;
        }

        final bool matchesDate =
            !transportDate.isBefore(stop.startDate) &&
            transportDate.isBefore(stop.endDate);

        if (!matchesDate) {
          continue;
        }

        print(
          'HOTEL FOR OUTBOUND TRANSFER FALLBACK: '
          'date=$transportDate, '
          'stop=${stop.city}, '
          'hotel=${hotel.name}, '
          'hotelId=${hotel.id}',
        );

        return hotel;
      }
    }

    print(
      'NO HOTEL FOR TRANSPORT: '
      'direction=${transport.direction}, '
      'date=$transportDate',
    );

    return null;
  }

  Future<void> loadTripStops() async {
    try {
      final stops = await TripStopService.getTripStops(widget.trip['id']);

      print('TRIP STOPS LOADED: ${stops.length}');

      for (final stop in stops) {
        print(
          'TRIP STOP: '
          'id=${stop.id}, '
          'city=${stop.city}, '
          'start=${stop.startDate}, '
          'end=${stop.endDate}',
        );
      }

      if (!mounted) return;

      setState(() {
        tripStops = stops;
        isLoadingTripStops = false;
      });
    } catch (e) {
      print('TRIP STOPS ERROR: $e');

      if (!mounted) return;

      setState(() {
        isLoadingTripStops = false;
      });
    }
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

        outboundTransferChoice =
            selectedOutboundTransports.any(
              (transport) => transport.type.startsWith('Transfer'),
            )
            ? 'Transfer'
            : null;

        returnTransferChoice =
            selectedReturnTransports.any(
              (transport) => transport.type.startsWith('Transfer'),
            )
            ? 'Transfer'
            : null;

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
      MaterialPageRoute(
        builder: (context) => TransportTypeSelectionPage(trip: trip),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport = result as Transport;

    for (final oldTransport in selectedOutboundTransports) {
      if (!oldTransport.type.startsWith('Transfer') &&
          oldTransport.id != null) {
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

    if (!mounted) {
      return;
    }

    await _offerTransfersForSelectedHotels(direction: 'outbound');
  }

  Future<void> chooseReturnTransport() async {
    final trip = {...widget.trip, 'return_transport': true};

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TransportTypeSelectionPage(trip: trip),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final transport = result as Transport;

    for (final oldTransport in selectedReturnTransports) {
      if (!oldTransport.type.startsWith('Transfer') &&
          oldTransport.id != null) {
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

    if (!mounted) {
      return;
    }

    await _offerTransfersForSelectedHotels(direction: 'return');
  }

  Future<void> _addTransfer({required Transport parentTransport}) async {
    final hotel = _getHotelForTransport(parentTransport);

    print(
      'TRANSFER HOTEL BEFORE PAGE: '
      'id=${hotel?.id}, '
      'name=${hotel?.name}, '
      'stopId=${hotel?.stopId}, '
      'lat=${hotel?.latitude}, '
      'lng=${hotel?.longitude}',
    );

    if (hotel == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Select a hotel for the relevant city before adding a transfer.',
          ),
        ),
      );
      return;
    }

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TransferSelectionPage(
          trip: widget.trip,
          parentTransport: parentTransport,
          selectedHotel: hotel,
        ),
      ),
    );

    if (!mounted || result == null) {
      return;
    }

    if (result is! Map) {
      return;
    }

    final resultType = result['type']?.toString();

    if (resultType != 'transfer') {
      return;
    }

    final option = Map<String, dynamic>.from(result['option'] as Map);

    final price = (option['price'] as num?)?.toDouble();

    if (price == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Transfer price is not available.')),
      );
      return;
    }

    final currency = option['currency']?.toString() ?? 'EUR';

    final vehicleName = option['vehicle_name']?.toString() ?? 'Transfer';

    final categoryName = option['category_name']?.toString() ?? '';

    final transferType = option['transfer_type']?.toString() ?? '';

    final transferName = [
      vehicleName,
      categoryName,
      transferType,
    ].where((value) => value.isNotEmpty).join(' · ');

    final bool isReturn = parentTransport.direction == 'return';

    final transfer = Transport(
      direction: parentTransport.direction,
      parentTransportId: parentTransport.id,
      transferData: {
        'vehicle_name': vehicleName,
        'category_name': categoryName,
        'transfer_type': transferType,
        'extras': option['extras'] is List
            ? List<Map<String, dynamic>>.from(
                (option['extras'] as List).map(
                  (item) => Map<String, dynamic>.from(item),
                ),
              )
            : <Map<String, dynamic>>[],
        'cancellation_policies': option['cancellation_policies'] is List
            ? List<Map<String, dynamic>>.from(
                (option['cancellation_policies'] as List).map(
                  (item) => Map<String, dynamic>.from(item),
                ),
              )
            : <Map<String, dynamic>>[],
      },
      type: transferName.isEmpty ? 'Transfer' : 'Transfer · $transferName',
      price: price,
      currency: currency,
      destinationPrice: price,
      destinationCurrency: currency,
      userPrice: price,
      userCurrency: currency,
      duration: 'Transfer',

      // Outbound: аэропорт прибытия → отель
      // Return: отель → аэропорт вылета
      departureDate: isReturn
          ? parentTransport.departureDate
          : parentTransport.arrivalDate,

      departureTime: isReturn
          ? parentTransport.departureTime
          : parentTransport.arrivalTime,

      departureLocation: isReturn
          ? hotel.name
          : parentTransport.arrivalLocation,

      arrivalDate: isReturn
          ? parentTransport.departureDate
          : parentTransport.arrivalDate,

      arrivalTime: isReturn
          ? parentTransport.departureTime
          : parentTransport.arrivalTime,

      arrivalLocation: isReturn
          ? parentTransport.departureLocation
          : hotel.name,
    );

    try {
      final existingTransfers = parentTransport.direction == 'return'
          ? selectedReturnTransports
                .where((transport) => transport.type.startsWith('Transfer'))
                .toList()
          : selectedOutboundTransports
                .where((transport) => transport.type.startsWith('Transfer'))
                .toList();

      for (final existingTransfer in existingTransfers) {
        if (existingTransfer.id != null) {
          await TransportService.deleteTransport(
            tripId: widget.trip['id'],
            transportId: existingTransfer.id!,
          );
        }
      }

      await TransportService.createTransport(
        tripId: widget.trip['id'],
        transport: transfer,
      );

      if (!mounted) return;

      if (parentTransport.direction == 'return') {
        returnTransferChoice = 'Transfer';
      } else {
        outboundTransferChoice = 'Transfer';
      }

      await loadSelectedTransports();
      await loadBudget();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to save transfer: $e')));
    }
  }

  Future<void> _deleteTransfer(Transport transfer) async {
    print(
      'DELETE TRANSFER CALLED: '
      'id=${transfer.id}, '
      'parent=${transfer.parentTransportId}, '
      'direction=${transfer.direction}, '
      'type=${transfer.type}',
    );

    if (transfer.id == null) {
      return;
    }

    try {
      await TransportService.deleteTransport(
        tripId: widget.trip['id'],
        transportId: transfer.id!,
      );

      if (!mounted) return;

      setState(() {
        if (transfer.direction == 'return') {
          selectedReturnTransports.removeWhere(
            (item) => item.id == transfer.id,
          );
          returnTransferChoice = null;
        } else {
          selectedOutboundTransports.removeWhere(
            (item) => item.id == transfer.id,
          );
          outboundTransferChoice = null;
        }
      });

      print(
        'AFTER DELETE LOCAL: '
        'returnTransfers=${selectedReturnTransports.map((item) => 'id=${item.id}, parent=${item.parentTransportId}, type=${item.type}').toList()} '
        'outboundTransfers=${selectedOutboundTransports.map((item) => 'id=${item.id}, parent=${item.parentTransportId}, type=${item.type}').toList()}',
      );

      await loadBudget();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Failed to delete transfer: $e')));
    }
  }

  // =========================
  // TRANSPORT CARD
  // =========================

  IconData getTransportIcon(String type) {
    if (type.startsWith('Flight')) {
      return Icons.flight;
    }

    if (type.startsWith('Bus')) {
      return Icons.directions_bus;
    }

    if (type.startsWith('Train')) {
      return Icons.train;
    }

    if (type.startsWith('Transfer')) {
      return Icons.directions_car;
    }

    return Icons.directions_transit;
  }

  Widget _buildTransferCard(Transport transport) {
    final bool isReturn = transport.direction == 'return';

    final String title = isReturn ? 'Hotel → Airport' : 'Airport → Hotel';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.directions_car,
                    color: Colors.blue,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Transfer',
                    style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                  ),
                ),
                Text(
                  '${transport.userPrice} ${transport.userCurrency}',
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 14),

            Text(
              title,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 6),

            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.location_on_outlined, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    transport.departureLocation,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),

            const Padding(
              padding: EdgeInsets.only(left: 9),
              child: SizedBox(
                height: 18,
                child: VerticalDivider(width: 1, thickness: 1),
              ),
            ),

            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.location_on, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    transport.arrivalLocation,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            Row(
              children: [
                Icon(
                  Icons.calendar_today_outlined,
                  size: 16,
                  color: Colors.grey.shade600,
                ),
                const SizedBox(width: 6),
                Text(
                  _formatDate(transport.departureDate),
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                ),
                const SizedBox(width: 12),
                Icon(Icons.access_time, size: 16, color: Colors.grey.shade600),
                const SizedBox(width: 6),
                Text(
                  transport.departureTime,
                  style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                ),
              ],
            ),

            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: Text(
                    transport.type,
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                  ),
                ),
                Text(
                  '${transport.destinationPrice} '
                  '${transport.destinationCurrency}',
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                ),
              ],
            ),

            const SizedBox(height: 8),

            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                onPressed: () {
                  print(
                    'DELETE BUTTON PRESSED: '
                    'id=${transport.id}, '
                    'parent=${transport.parentTransportId}, '
                    'direction=${transport.direction}',
                  );

                  _deleteTransfer(transport);
                },
                icon: const Icon(Icons.delete_outline, color: Colors.red),
                label: const Text(
                  'Delete transfer',
                  style: TextStyle(color: Colors.red),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildTransportCard(
    Transport transport, {
    required VoidCallback onChange,
    VoidCallback? onTap,
    String? transferChoice,
    VoidCallback? onAddTransfer,
  }) {
    print(
      'BUILD TRANSPORT CARD: '
      'id=${transport.id}, '
      'direction=${transport.direction}, '
      'type=${transport.type}, '
      'transferChoice=$transferChoice',
    );
    final bool isReturn = transport.direction == 'return';
    final bool isTransfer = transport.type.startsWith('Transfer');
    if (isTransfer) {
      return _buildTransferCard(transport);
    }

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
      clipBehavior: Clip.antiAlias,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
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
                              '${transport.userPrice} '
                              '${transport.userCurrency}',
                              textAlign: TextAlign.right,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '${transport.destinationPrice} '
                              '${transport.destinationCurrency}',
                              textAlign: TextAlign.right,
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.grey.shade600,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                OutlinedButton(
                                  onPressed: isTransfer ? null : onChange,
                                  child: const Text('Change'),
                                ),
                                if (!isTransfer && onAddTransfer != null) ...[
                                  const SizedBox(height: 6),
                                  OutlinedButton(
                                    onPressed: onAddTransfer,
                                    style: OutlinedButton.styleFrom(
                                      minimumSize: const Size(48, 42),
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 10,
                                        vertical: 8,
                                      ),
                                      side: BorderSide(
                                        color: transferChoice != null
                                            ? Colors.blue
                                            : Colors.grey.shade400,
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                    ),
                                    child: Icon(
                                      transferChoice == 'Transfer'
                                          ? Icons.directions_car
                                          : transferChoice == 'Build a route'
                                          ? Icons.alt_route
                                          : Icons.directions_car_outlined,
                                      color:
                                          transferChoice == 'Transfer' ||
                                              transferChoice == 'Build a route'
                                          ? Colors.blue
                                          : Colors.grey.shade600,
                                      size: 24,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '${_formatDate(transport.departureDate)} → ${_formatDate(transport.arrivalDate)}',
                      style: const TextStyle(fontSize: 14),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${transport.departureTime} → '
                      '${transport.arrivalTime}',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      transport.duration,
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    if (transport.segments.length > 1) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Connections: ${transport.segments.take(transport.segments.length - 1).map((segment) => segment.arrivalLocation).join(' → ')}',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                    if (isTransfer) ...[
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerRight,
                        child: OutlinedButton.icon(
                          onPressed: () {
                            print(
                              'DELETE BUTTON PRESSED: '
                              'id=${transport.id}, '
                              'parent=${transport.parentTransportId}, '
                              'direction=${transport.direction}',
                            );

                            _deleteTransfer(transport);
                          },
                          icon: const Icon(
                            Icons.delete_outline,
                            color: Colors.red,
                          ),
                          label: const Text(
                            'Delete transfer',
                            style: TextStyle(color: Colors.red),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
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

      for (final hotel in hotels) {
        print(
          'HOTEL: id=${hotel.id}, '
          'name=${hotel.name}, '
          'stopId=${hotel.stopId}, '
          'lat=${hotel.latitude}, '
          'lng=${hotel.longitude}',
        );
      }

      if (!mounted) return;

      final mainHotel = hotels.where((hotel) => hotel.stopId == null).toList();

      final stopHotels = <int, Hotel>{};

      for (final hotel in hotels) {
        if (hotel.stopId != null) {
          stopHotels[hotel.stopId!] = hotel;
        }
      }

      setState(() {
        // Temporary legacy hotel.
        // It is not displayed as a separate hotel section anymore.
        // It is still required by the current transfer flow.
        selectedHotel = mainHotel.isNotEmpty ? mainHotel.last : null;

        selectedStopHotels = stopHotels;
        isLoadingHotel = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoadingHotel = false;
      });
    }
  }

  bool _hasTransferForTransport(Transport transport) {
    final transports = transport.direction == 'return'
        ? selectedReturnTransports
        : selectedOutboundTransports;

    final matchingTransfers = transports
        .where(
          (item) =>
              item.type.startsWith('Transfer') &&
              item.parentTransportId == transport.id,
        )
        .toList();

    print(
      'CHECK TRANSFER: '
      'transportId=${transport.id}, '
      'direction=${transport.direction}, '
      'matchingTransfers=${matchingTransfers.map((item) => 'id=${item.id}, parent=${item.parentTransportId}').toList()}',
    );

    return matchingTransfers.isNotEmpty;
  }

  Future<void> _offerTransfersForSelectedHotels({String? direction}) async {
    await loadSelectedHotel();

    if (!mounted) {
      return;
    }

    final hotels = selectedStopHotels.values.toList();

    if (hotels.isEmpty) {
      return;
    }

    for (final hotel in hotels) {
      if (!mounted) {
        return;
      }

      await _offerTransfersForHotel(hotel, direction: direction);
    }
  }

  Future<void> _offerTransfersForHotel(Hotel hotel, {String? direction}) async {
    await loadSelectedTransports();

    if (!mounted) {
      return;
    }

    final outbound = selectedOutboundTransports
        .where((transport) => !transport.type.startsWith('Transfer'))
        .toList();

    final returns = selectedReturnTransports
        .where((transport) => !transport.type.startsWith('Transfer'))
        .toList();

    List<Transport> relevantOutbound = [];
    List<Transport> relevantReturns = [];

    // Если это гостиница конкретного TripStop,
    // связываем трансферы именно с этим stop.
    if (hotel.stopId != null) {
      final stop = tripStops.cast<TripStop?>().firstWhere(
        (item) => item?.id == hotel.stopId,
        orElse: () => null,
      );

      if (stop != null) {
        relevantOutbound = outbound.where((transport) {
          final arrivalDate = DateTime.tryParse(transport.arrivalDate);

          if (arrivalDate == null) {
            return false;
          }

          return !arrivalDate.isAfter(stop.endDate) &&
              !arrivalDate.isBefore(stop.startDate);
        }).toList();

        relevantReturns = returns.where((transport) {
          final departureDate = DateTime.tryParse(transport.departureDate);

          if (departureDate == null) {
            return false;
          }

          return !departureDate.isBefore(stop.startDate) &&
              !departureDate.isAfter(stop.endDate);
        }).toList();
      }
    } else {
      // Legacy / single-hotel trip:
      // гостиница относится ко всему путешествию.
      relevantOutbound = outbound;
      relevantReturns = returns;
    }

    // Сначала предлагаем трансфер аэропорт → отель.
    if (direction == null || direction == 'outbound') {
      for (final transport in relevantOutbound) {
        if (_hasTransferForTransport(transport)) {
          continue;
        }

        final addTransfer = await TripDialogs.showAddTransferDialog(
          context,
          isReturn: false,
        );

        if (!mounted) {
          return;
        }

        if (addTransfer) {
          await _addTransfer(parentTransport: transport);
          await loadSelectedTransports();
        }
      }
    }

    // Затем предлагаем трансфер отель → аэропорт.
    if (direction == null || direction == 'return') {
      for (final transport in relevantReturns) {
        if (_hasTransferForTransport(transport)) {
          continue;
        }

        final addTransfer = await TripDialogs.showAddTransferDialog(
          context,
          isReturn: true,
        );

        if (!mounted) {
          return;
        }

        if (addTransfer) {
          await _addTransfer(parentTransport: transport);
          await loadSelectedTransports();
        }
      }
    }
  }

  Future<void> chooseStopHotel(TripStop stop) async {
    final result = await Navigator.push<Object?>(
      context,
      MaterialPageRoute(
        builder: (context) => HotelOptionsPage(trip: widget.trip, stop: stop),
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    if (result is bool && result) {
      await loadSelectedHotel();
      await loadSelectedTransports();
      await loadBudget();

      return;
    }

    if (result is! Hotel) {
      return;
    }

    setState(() {
      selectedStopHotels[stop.id] = result;
    });

    await loadSelectedTransports();
    await loadTripStops();
    await loadBudget();

    if (!mounted) {
      return;
    }

    await _offerTransfersForHotel(result);
  }

  Future<void> openStopHotelDetails(TripStop stop) async {
    final hotel = selectedStopHotels[stop.id];

    if (hotel == null) {
      return;
    }

    final stopIndex = tripStops.indexWhere((item) => item.id == stop.id);

    final TripStop? nextStop =
        stopIndex >= 0 && stopIndex + 1 < tripStops.length
        ? tripStops[stopIndex + 1]
        : null;

    final result = await Navigator.push<Object?>(
      context,
      MaterialPageRoute(
        builder: (context) => HotelDetailsPage(
          hotel: hotel,
          trip: widget.trip,
          stop: stop,
          nextStop: nextStop,
        ),
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    if (result is bool && result) {
      await loadSelectedHotel();
      await loadSelectedTransports();
      await loadBudget();

      return;
    }

    if (result is! Hotel) {
      return;
    }

    final tripId = widget.trip['id'];

    try {
      final savedHotel = await HotelService.createHotel(
        tripId: tripId,
        hotel: result,
        stopId: stop.id,
      );

      if (!mounted) return;

      setState(() {
        selectedStopHotels[stop.id] = savedHotel;
      });

      await loadBudget();

      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Hotel updated')));
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to update hotel: $e')));
    }
  }

  Future<void> _deleteTransfersForStop(TripStop stop) async {
    print(
      'DELETE TRANSFERS FOR STOP: '
      'stopId=${stop.id}, '
      'start=${stop.startDate}, '
      'end=${stop.endDate}',
    );

    await loadSelectedTransports();

    if (!mounted) {
      return;
    }

    final allTransports = [
      ...selectedOutboundTransports,
      ...selectedReturnTransports,
    ];

    print(
      'ALL TRANSPORTS: '
      '${allTransports.map((transport) => 'id=${transport.id}, '
          'type=${transport.type}, '
          'direction=${transport.direction}, '
          'parent=${transport.parentTransportId}, '
          'departure=${transport.departureDate}, '
          'arrival=${transport.arrivalDate}').toList()}',
    );

    final flights = allTransports.where((transport) {
      if (transport.type.startsWith('Transfer')) {
        return false;
      }

      if (transport.direction == 'outbound') {
        final arrivalDate = DateTime.tryParse(transport.arrivalDate);

        if (arrivalDate == null) {
          return false;
        }

        return !arrivalDate.isBefore(stop.startDate) &&
            !arrivalDate.isAfter(stop.endDate);
      }

      if (transport.direction == 'return') {
        final departureDate = DateTime.tryParse(transport.departureDate);

        if (departureDate == null) {
          return false;
        }

        return !departureDate.isBefore(stop.startDate) &&
            !departureDate.isAfter(stop.endDate);
      }

      return false;
    }).toList();

    print(
      'FLIGHTS FOR STOP: '
      '${flights.map((transport) => 'id=${transport.id}, '
          'direction=${transport.direction}, '
          'departure=${transport.departureDate}, '
          'arrival=${transport.arrivalDate}').toList()}',
    );

    final flightIds = flights
        .where((transport) => transport.id != null)
        .map((transport) => transport.id!)
        .toSet();

    final transfers = allTransports.where((transport) {
      return transport.type.startsWith('Transfer') &&
          transport.parentTransportId != null &&
          flightIds.contains(transport.parentTransportId);
    }).toList();

    print(
      'TRANSFERS FOR STOP: '
      '${transfers.map((transfer) => 'id=${transfer.id}, '
          'parent=${transfer.parentTransportId}, '
          'type=${transfer.type}').toList()}',
    );

    for (final transfer in transfers) {
      if (transfer.id == null) {
        continue;
      }

      print(
        'DELETE TRANSFER: '
        'id=${transfer.id}, '
        'parent=${transfer.parentTransportId}',
      );

      await TransportService.deleteTransport(
        tripId: widget.trip['id'],
        transportId: transfer.id!,
      );
    }

    if (transfers.isNotEmpty) {
      await loadSelectedTransports();
      await loadBudget();
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

    final userAmount = value['user_amount'];
    final userCurrency = value['user_currency'];

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontSize: isTotal ? 16 : 14,
                fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (userAmount != null && userCurrency != null)
                Text(
                  '${userAmount.toStringAsFixed(2)} '
                  '$userCurrency',
                  style: TextStyle(
                    fontSize: isTotal ? 16 : 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              if (userAmount != null && userCurrency != null)
                Text(
                  '(${amount.toStringAsFixed(2)} $currency)',
                  style: TextStyle(
                    fontSize: isTotal ? 12 : 11,
                    color: Colors.grey.shade600,
                  ),
                )
              else
                Text(
                  '${amount.toStringAsFixed(2)} $currency',
                  style: TextStyle(
                    fontSize: isTotal ? 16 : 14,
                    fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
            ],
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

      final savedPlaces = await PlaceService.createPlacesBulk(
        tripId: tripId,
        places: places,
      );

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

  Future<void> addPlaces() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => PlaceOptionsPage(
          trip: widget.trip,
          initialSelectedPlaces: selectedPlaces,
        ),
      ),
    );

    if (result == null || !context.mounted) {
      return;
    }

    final places = List<Place>.from(result);

    final existingIds = selectedPlaces
        .where((place) => place.id != null)
        .map((place) => place.id!)
        .toSet();

    final newPlaces = places.where((place) {
      return place.id == null || !existingIds.contains(place.id);
    }).toList();

    if (newPlaces.isEmpty) {
      return;
    }

    final tripId = widget.trip['id'];

    try {
      final savedPlaces = await PlaceService.createPlacesBulk(
        tripId: tripId,
        places: newPlaces,
      );

      if (!context.mounted) return;

      setState(() {
        selectedPlaces.addAll(savedPlaces);
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Places added')));
    } catch (e) {
      if (!context.mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Failed to add places: $e')));
    }
  }

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

  Widget buildTripStopsSection() {
    if (isLoadingTripStops) {
      return const Center(child: CircularProgressIndicator());
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Cities',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                TextButton.icon(
                  onPressed: addTripStop,
                  icon: const Icon(Icons.add),
                  label: const Text('Add city'),
                ),
              ],
            ),

            const SizedBox(height: 8),

            if (tripStops.isEmpty)
              const Text(
                'No additional cities',
                style: TextStyle(color: Colors.grey),
              ),

            ...tripStops.asMap().entries.map((entry) {
              final index = entry.key;
              final stop = entry.value;

              final hotel = selectedStopHotels[stop.id];

              TripStop? nextStop;

              if (index + 1 < tripStops.length) {
                nextStop = tripStops[index + 1];
              }

              final nextHotel = nextStop == null
                  ? null
                  : selectedStopHotels[nextStop.id];

              final bool hasIntercityTransfer =
                  hotel != null &&
                  nextStop != null &&
                  nextHotel != null &&
                  stop.city.trim().toLowerCase() !=
                      nextStop!.city.trim().toLowerCase();

              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.location_city),
                        title: Text(stop.city),
                        subtitle: Text(
                          '${stop.startDate.day.toString().padLeft(2, '0')}.'
                          '${stop.startDate.month.toString().padLeft(2, '0')}.'
                          '${stop.startDate.year}'
                          ' — '
                          '${stop.endDate.day.toString().padLeft(2, '0')}.'
                          '${stop.endDate.month.toString().padLeft(2, '0')}.'
                          '${stop.endDate.year}',
                        ),
                        trailing: IconButton(
                          icon: const Icon(
                            Icons.delete_outline,
                            color: Colors.red,
                          ),
                          onPressed: () async {
                            await TripStopService.deleteTripStop(
                              tripId: widget.trip['id'],
                              stopId: stop.id,
                            );

                            await loadTripStops();
                            await loadSelectedHotel();
                            await loadSelectedTransports();
                            await loadBudget();
                          },
                        ),
                      ),

                      const Divider(),

                      if (hotel == null)
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () => chooseStopHotel(stop),
                            icon: const Icon(Icons.hotel_outlined),
                            label: Text('Choose hotel in ${stop.city}'),
                          ),
                        )
                      else
                        InkWell(
                          onTap: () => openStopHotelDetails(stop),
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Padding(
                                  padding: EdgeInsets.only(top: 4),
                                  child: Icon(Icons.hotel),
                                ),

                                const SizedBox(width: 12),

                                Expanded(
                                  child: Padding(
                                    padding: const EdgeInsets.only(top: 2),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          hotel.name,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          '${hotel.userPrice.toStringAsFixed(2)} '
                                          '${hotel.userCurrency}',
                                          style: TextStyle(
                                            fontSize: 14,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),

                                const SizedBox(width: 8),

                                Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    OutlinedButton(
                                      onPressed: () => chooseStopHotel(stop),
                                      style: OutlinedButton.styleFrom(
                                        minimumSize: const Size(0, 40),
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 14,
                                          vertical: 8,
                                        ),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            20,
                                          ),
                                        ),
                                      ),
                                      child: const Text('Change'),
                                    ),

                                    if (hasIntercityTransfer) ...[
                                      const SizedBox(height: 6),
                                      SizedBox(
                                        width: 40,
                                        height: 40,
                                        child: OutlinedButton(
                                          onPressed: () =>
                                              openStopHotelDetails(stop),
                                          style: OutlinedButton.styleFrom(
                                            padding: const EdgeInsets.all(0),
                                            minimumSize: const Size(40, 40),
                                            side: BorderSide(
                                              color: Colors.grey.shade400,
                                            ),
                                            shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(10),
                                            ),
                                          ),
                                          child: const Icon(
                                            Icons.directions_car_outlined,
                                            color: Colors.grey,
                                            size: 24,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              );
            }),
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

    final outboundMainTransport = selectedOutboundTransports
        .where((transport) => !transport.type.startsWith('Transfer'))
        .toList();

    final returnMainTransport = selectedReturnTransports
        .where((transport) => !transport.type.startsWith('Transfer'))
        .toList();

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
              '${_formatDate(widget.trip['start_date'])} → '
              '${_formatDate(widget.trip['end_date'])}',
              style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 24),

            buildTripStopsSection(),

            const SizedBox(height: 16),

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
            else if (outboundMainTransport.isNotEmpty)
              ...outboundMainTransport.map(
                (transport) => buildTransportCard(
                  transport,
                  onChange: chooseOutboundTransport,
                  transferChoice: _hasTransferForTransport(transport)
                      ? 'Transfer'
                      : null,
                  onAddTransfer: () => _addTransfer(parentTransport: transport),
                  onTap: () async {
                    final result = await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) {
                          final hotel = _getHotelForTransport(transport);

                          return TransportDetailsPage(
                            trip: widget.trip,
                            transport: transport,
                            hasSelectedHotel: hotel != null,
                            selectedHotel: hotel,
                            onAddTransfer: () =>
                                _addTransfer(parentTransport: transport),
                          );
                        },
                      ),
                    );

                    if (result == true && mounted) {
                      await loadSelectedTransports();
                      await loadBudget();
                    }
                  },
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
            else if (returnMainTransport.isNotEmpty)
              ...returnMainTransport.map(
                (transport) => buildTransportCard(
                  transport,
                  onChange: chooseReturnTransport,
                  transferChoice: _hasTransferForTransport(transport)
                      ? 'Transfer'
                      : null,
                  onAddTransfer: () => _addTransfer(parentTransport: transport),
                  onTap: () async {
                    final result = await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) {
                          final hotel = _getHotelForTransport(transport);

                          return TransportDetailsPage(
                            trip: widget.trip,
                            transport: transport,
                            hasSelectedHotel: hotel != null,
                            selectedHotel: hotel,
                          );
                        },
                      ),
                    );

                    if (result == true && mounted) {
                      await loadSelectedTransports();
                      await loadBudget();
                    }
                  },
                ),
              )
            else
              ElevatedButton(
                onPressed: chooseReturnTransport,
                child: const Text('Choose return transport'),
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
                  childAspectRatio: 4.5,
                ),
                itemBuilder: (context, index) {
                  return buildPlaceCard(selectedPlaces[index]);
                },
              ),

              const SizedBox(height: 8),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: addPlaces,
                      child: const Text('Add places'),
                    ),
                  ),

                  const SizedBox(width: 10),

                  Expanded(
                    child: OutlinedButton(
                      onPressed: choosePlaces,
                      child: const Text('Change places'),
                    ),
                  ),
                ],
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

                      _buildBudgetRow(
                        'Total in your currency',
                        budget!['user_total'],
                        isTotal: true,
                      ),

                      const SizedBox(height: 8),

                      _buildBudgetRow(
                        'Total in destination currency',
                        budget!['total'],
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
            // ITINERARY OPTIONS
            // =========================
            const Text(
              'Itinerary options',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            Text(
              'Choose whether activities can be planned on your arrival and departure days.',
              style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
            ),

            const SizedBox(height: 8),

            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: includeArrivalDayActivities,
              onChanged: (value) {
                setState(() {
                  includeArrivalDayActivities = value ?? false;
                });
              },
              title: const Text('Plan activities on arrival day'),
            ),

            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: includeDepartureDayActivities,
              onChanged: (value) {
                setState(() {
                  includeDepartureDayActivities = value ?? false;
                });
              },
              title: const Text('Plan activities on departure day'),
            ),

            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ItineraryPage(
                        trip: widget.trip,
                        includeArrivalDayActivities:
                            includeArrivalDayActivities,
                        includeDepartureDayActivities:
                            includeDepartureDayActivities,
                      ),
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
