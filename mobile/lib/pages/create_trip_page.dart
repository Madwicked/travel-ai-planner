import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/location.dart';
import '../services/api_service.dart';

class CreateTripPage extends StatefulWidget {
  const CreateTripPage({super.key});

  @override
  State<CreateTripPage> createState() => _CreateTripPageState();
}

class _CreateTripPageState extends State<CreateTripPage> {
  final originController = TextEditingController();
  final destinationController = TextEditingController();

  Location? selectedOrigin;
  int _citySearchRequestId = 0;
  Location? selectedDestination;

  bool originSelected = false;
  bool destinationSelected = false;

  DateTime? startDate;
  DateTime? endDate;

  int travelers = 1;

  bool isLoading = false;

  Future<String> getUserCurrency() async {
    final prefs = await SharedPreferences.getInstance();

    final savedCurrency = prefs.getString('user_currency');

    if (savedCurrency != null && savedCurrency.isNotEmpty) {
      return savedCurrency;
    }

    final locale = WidgetsBinding.instance.platformDispatcher.locale;

    String currency;

    switch (locale.countryCode) {
      case 'RS':
        currency = 'RSD';
        break;
      case 'US':
        currency = 'USD';
        break;
      case 'GB':
        currency = 'GBP';
        break;
      case 'CH':
        currency = 'CHF';
        break;
      case 'CA':
        currency = 'CAD';
        break;
      case 'AU':
        currency = 'AUD';
        break;
      case 'JP':
        currency = 'JPY';
        break;
      case 'CN':
        currency = 'CNY';
        break;
      case 'TR':
        currency = 'TRY';
        break;
      case 'AE':
        currency = 'AED';
        break;
      case 'TH':
        currency = 'THB';
        break;
      default:
        currency = 'EUR';
    }

    await prefs.setString('user_currency', currency);

    return currency;
  }

  Future<void> selectDate(bool isStartDate) async {
    final now = DateTime.now();

    final firstDate = isStartDate ? now : (startDate ?? now);

    final initialDate = isStartDate
        ? (startDate ?? now)
        : (endDate ?? startDate ?? now);

    final result = await showDialog<DateTime>(
      context: context,
      builder: (context) {
        return Dialog(
          child: CalendarDatePicker(
            initialDate: initialDate.isBefore(firstDate)
                ? firstDate
                : initialDate,
            firstDate: firstDate,
            lastDate: now.add(const Duration(days: 730)),
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

        if (endDate != null && !endDate!.isAfter(result)) {
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

  Future<void> generateTrip() async {
    if (originController.text.trim().isEmpty ||
        destinationController.text.trim().isEmpty ||
        startDate == null ||
        endDate == null ||
        selectedOrigin == null ||
        selectedDestination == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Please select cities from the suggestions and fill in all fields.',
          ),
        ),
      );
      return;
    }

    if (!endDate!.isAfter(startDate!)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('End date must be after the start date.')),
      );
      return;
    }

    setState(() {
      isLoading = true;
    });

    try {
      final userCurrency = await getUserCurrency();

      final data = await ApiService.createTrip(
        origin: selectedOrigin!.name,
        originCountry: selectedOrigin!.country,
        originLatitude: selectedOrigin!.latitude,
        originLongitude: selectedOrigin!.longitude,
        destination: selectedDestination!.name,
        destinationCountry: selectedDestination!.country,
        destinationLatitude: selectedDestination!.latitude,
        destinationLongitude: selectedDestination!.longitude,
        startDate: startDate!.toIso8601String().split('T').first,
        endDate: endDate!.toIso8601String().split('T').first,
        travelers: travelers,
      );

      final tripId = data['trip_id'];

      await ApiService.updateUserCurrency(
        tripId: tripId,
        userCurrency: userCurrency,
      );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Trip created! ID: $tripId')));

      Navigator.of(context).pop(true);
    } catch (e) {
      print('Connection error: $e');

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('Connection error: $e')));
    } finally {
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    originController.dispose();
    destinationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Create Trip',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Plan your perfect trip ✈️',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 8),

              Text(
                'Tell us about your trip and AI will create '
                'a personalized itinerary.',
                style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
              ),

              const SizedBox(height: 28),

              const Text(
                'From',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              RawAutocomplete<Location>(
                optionsBuilder: (TextEditingValue textEditingValue) async {
                  final query = textEditingValue.text.trim();

                  if (query.length < 2 || originSelected) {
                    return const Iterable<Location>.empty();
                  }

                  final requestId = ++_citySearchRequestId;

                  final cities = await ApiService.searchCities(query);

                  if (requestId != _citySearchRequestId) {
                    return const Iterable<Location>.empty();
                  }

                  return cities.map((city) => Location.fromJson(city));
                },
                displayStringForOption: (city) {
                  return city.displayName;
                },
                onSelected: (city) {
                  selectedOrigin = city;
                  originSelected = true;

                  setState(() {});
                },
                fieldViewBuilder:
                    (context, controller, focusNode, onFieldSubmitted) {
                      return TextField(
                        controller: controller,
                        focusNode: focusNode,
                        onChanged: (value) {
                          originController.text = value;

                          if (originSelected &&
                              value != selectedOrigin?.displayName) {
                            originSelected = false;
                            selectedOrigin = null;
                          }

                          setState(() {});
                        },
                        decoration: InputDecoration(
                          hintText: 'e.g. Belgrade, Serbia',
                          prefixIcon: const Icon(Icons.flight_takeoff),
                          suffixIcon: controller.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    controller.clear();
                                    originController.clear();
                                    selectedOrigin = null;
                                    originSelected = false;

                                    setState(() {});
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
                  if (originSelected) {
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
                'To',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              RawAutocomplete<Location>(
                optionsBuilder: (TextEditingValue textEditingValue) async {
                  final query = textEditingValue.text.trim();

                  if (query.length < 2 || destinationSelected) {
                    return const Iterable<Location>.empty();
                  }

                  final requestId = ++_citySearchRequestId;

                  await Future.delayed(const Duration(milliseconds: 400));

                  if (requestId != _citySearchRequestId) {
                    return const Iterable<Location>.empty();
                  }

                  final cities = await ApiService.searchCities(query);

                  if (requestId != _citySearchRequestId) {
                    return const Iterable<Location>.empty();
                  }

                  return cities.map((city) => Location.fromJson(city));
                },
                displayStringForOption: (city) {
                  return city.displayName;
                },
                onSelected: (city) {
                  selectedDestination = city;
                  destinationSelected = true;

                  setState(() {});
                },
                fieldViewBuilder:
                    (context, controller, focusNode, onFieldSubmitted) {
                      return TextField(
                        controller: controller,
                        focusNode: focusNode,
                        onChanged: (value) {
                          destinationController.text = value;

                          if (destinationSelected &&
                              value != selectedDestination?.displayName) {
                            destinationSelected = false;
                            selectedDestination = null;
                          }

                          setState(() {});
                        },
                        decoration: InputDecoration(
                          hintText: 'e.g. Rome, Italy',
                          prefixIcon: const Icon(Icons.location_on_outlined),
                          suffixIcon: controller.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    controller.clear();
                                    destinationController.clear();
                                    selectedDestination = null;
                                    destinationSelected = false;

                                    setState(() {});
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
                  if (destinationSelected) {
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
                'Travel dates',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isLoading ? null : () => selectDate(true),
                      icon: const Icon(Icons.calendar_today),
                      label: Text(formatDate(startDate)),
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: isLoading ? null : () => selectDate(false),
                      icon: const Icon(Icons.calendar_today),
                      label: Text(formatDate(endDate)),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              const Text(
                'Travelers',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),

              const SizedBox(height: 8),

              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade400),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    IconButton(
                      onPressed: isLoading || travelers <= 1
                          ? null
                          : () {
                              setState(() {
                                travelers--;
                              });
                            },
                      icon: const Icon(Icons.remove),
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
                      icon: const Icon(Icons.add),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              SizedBox(
                width: double.infinity,
                height: 54,
                child: FilledButton.icon(
                  onPressed: isLoading ? null : generateTrip,
                  icon: isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.auto_awesome),
                  label: Text(
                    isLoading ? 'Generating...' : 'Generate My Trip',
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
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
