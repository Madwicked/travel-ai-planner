import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import '../models/place.dart';
import '../services/place_service.dart';

class PlaceOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;

  const PlaceOptionsPage({super.key, required this.trip});

  @override
  State<PlaceOptionsPage> createState() => _PlaceOptionsPageState();
}

class _PlaceOptionsPageState extends State<PlaceOptionsPage> {
  List<Place> options = [];
  final Set<int> selectedIndexes = {};

  bool isLoading = true;
  String? errorMessage;

  bool isListView = false;

  String selectedCategory = 'All';
  double radiusKm = 5;
  double appliedRadiusKm = 5;

  final categories = <String>[
    'All',
    'Culture',
    'Food',
    'Beach',
    'Nature',
    'Nightlife',
    'Shopping',
  ];

  Future<void> loadPlaceOptions() async {
    final tripId = widget.trip['id'];

    try {
      final loadedOptions = await PlaceService.getPlaceOptions(
        tripId,
        appliedRadiusKm.round(),
      );

      if (!mounted) return;

      setState(() {
        options = loadedOptions;
        isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load place options';
        isLoading = false;
      });
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

  void togglePlace(int index) {
    setState(() {
      if (selectedIndexes.contains(index)) {
        selectedIndexes.remove(index);
      } else {
        selectedIndexes.add(index);
      }
    });
  }

  void savePlaces() {
    final selectedPlaces = selectedIndexes
        .map((index) => options[index])
        .toList();

    Navigator.pop(context, selectedPlaces);
  }

  List<Place> get filteredOptions {
    final filteredIndexes = <int>[];

    for (var index = 0; index < options.length; index++) {
      final place = options[index];

      if (selectedCategory == 'All' || place.category == selectedCategory) {
        filteredIndexes.add(index);
      }
    }

    final selected = filteredIndexes
        .where((index) => selectedIndexes.contains(index))
        .toList();

    final unselected = filteredIndexes
        .where((index) => !selectedIndexes.contains(index))
        .toList();

    selected.sort(
      (a, b) => options[a].name.toLowerCase().compareTo(
        options[b].name.toLowerCase(),
      ),
    );

    unselected.sort(
      (a, b) => options[a].name.toLowerCase().compareTo(
        options[b].name.toLowerCase(),
      ),
    );

    return [
      ...selected.map((index) => options[index]),
      ...unselected.map((index) => options[index]),
    ];
  }

  Widget buildCardView() {
    return Column(
      children: filteredOptions.asMap().entries.map((entry) {
        final option = entry.value;
        final originalIndex = options.indexOf(option);
        final isSelected = selectedIndexes.contains(originalIndex);

        return Card(
          margin: const EdgeInsets.only(bottom: 6),
          elevation: isSelected ? 3 : 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: isSelected
                ? const BorderSide(color: Colors.blue, width: 2)
                : BorderSide.none,
          ),
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => togglePlace(originalIndex),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      getPlaceIcon(option.category),
                      color: Colors.blue,
                      size: 24,
                    ),
                  ),

                  const SizedBox(width: 12),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          option.name,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),

                        const SizedBox(height: 3),

                        Row(
                          children: [
                            Text(
                              option.category,
                              style: TextStyle(
                                fontSize: 13,
                                color: Colors.grey.shade700,
                              ),
                            ),

                            if (option.distanceKm != null) ...[
                              const SizedBox(width: 8),

                              Text(
                                '• ${option.distanceKm!.toStringAsFixed(1)} km',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                            ],
                          ],
                        ),

                        const SizedBox(height: 3),

                        Text(
                          option.address,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
                        ),

                        const SizedBox(height: 6),

                        Row(
                          children: [
                            Text(
                              '${option.openingTime}–'
                              '${option.closingTime}',
                              style: const TextStyle(fontSize: 12),
                            ),

                            const SizedBox(width: 12),

                            Text(
                              'Visit: '
                              '${option.visitDuration ?? '-'}',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(width: 6),

                  Checkbox(
                    value: isSelected,
                    onChanged: (_) => togglePlace(originalIndex),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget buildListView() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: filteredOptions.asMap().entries.map((entry) {
          final option = entry.value;
          final originalIndex = options.indexOf(option);
          final isSelected = selectedIndexes.contains(originalIndex);

          return ListTile(
            leading: Icon(getPlaceIcon(option.category), color: Colors.blue),

            title: Text(
              option.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),

            subtitle: Text(
              '${option.category} • '
              '${option.address}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),

            trailing: Checkbox(
              value: isSelected,
              onChanged: (_) => togglePlace(originalIndex),
            ),

            onTap: () => togglePlace(originalIndex),
          );
        }).toList(),
      ),
    );
  }

  @override
  void initState() {
    super.initState();

    loadPlaceOptions();
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          context.tr('Places to Visit'),
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),

      body: _buildBody(destination),

      bottomNavigationBar: isLoading
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: selectedIndexes.isEmpty ? null : savePlaces,
                    child: Text(
                      selectedIndexes.isEmpty
                          ? context.tr('Save Places')
                          : '${context.tr('Save Places')} '
                                '(${selectedIndexes.length})',
                    ),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _buildBody(String destination) {
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

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 100),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            destination,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          Text(
            'Choose places you want to visit',
            style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
          ),
          const SizedBox(height: 16),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Distance',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              Text(
                '${radiusKm.round()} km',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          Slider(
            value: radiusKm,
            min: 1,
            max: 10,
            divisions: 9,
            label: '${radiusKm.round()} km',
            onChanged: (value) {
              setState(() {
                radiusKm = value;
              });
            },
          ),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: isLoading
                  ? null
                  : () {
                      setState(() {
                        appliedRadiusKm = radiusKm;
                        isLoading = true;
                      });

                      loadPlaceOptions();
                    },
              child: Text('Apply ${radiusKm.round()} km'),
            ),
          ),
          const SizedBox(height: 20),

          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment<bool>(
                    value: false,
                    icon: Icon(Icons.grid_view),
                    label: Text('Cards'),
                  ),
                  ButtonSegment<bool>(
                    value: true,
                    icon: Icon(Icons.view_list),
                    label: Text('List'),
                  ),
                ],
                selected: {isListView},
                onSelectionChanged: (selection) {
                  setState(() {
                    isListView = selection.first;
                  });
                },
              ),
            ],
          ),

          const SizedBox(height: 16),

          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: categories.map((category) {
                final isSelected = selectedCategory == category;

                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(category),
                    selected: isSelected,
                    onSelected: (_) {
                      setState(() {
                        selectedCategory = category;
                      });
                    },
                  ),
                );
              }).toList(),
            ),
          ),

          const SizedBox(height: 16),

          isListView ? buildListView() : buildCardView(),
        ],
      ),
    );
  }
}
