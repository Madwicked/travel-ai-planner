import 'package:flutter/material.dart';

import '../widgets/places_map.dart';
import '../models/place.dart';
import '../services/place_service.dart';

class PlaceOptionsPage extends StatefulWidget {
  final Map<String, dynamic> trip;
  final List<Place> initialSelectedPlaces;

  const PlaceOptionsPage({
    super.key,
    required this.trip,
    this.initialSelectedPlaces = const [],
  });

  @override
  State<PlaceOptionsPage> createState() => _PlaceOptionsPageState();
}

class _PlaceOptionsPageState extends State<PlaceOptionsPage> {
  bool get isAddingPlaces => widget.initialSelectedPlaces.isNotEmpty;

  List<Place> options = [];

  final Set<int> selectedIndexes = {};
  final Set<String> selectedPlaceIds = {};

  bool isLoading = true;
  String? errorMessage;

  bool isListView = false;

  String searchType = 'city';

  bool useRadius = false;
  double radiusKm = 5;

  Set<String> selectedCategories = {'All'};

  final categories = <String>[
    'All',
    'Attractions',
    'Nature',
    'Entertainment',
    'Food',
    'Shopping',
  ];

  final TextEditingController nameSearchController = TextEditingController();

  final ScrollController _scrollController = ScrollController();
  bool _showScrollToTop = false;

  String nameSearch = '';
  String selectedSort = 'Significance';

  int currentOffset = 0;
  int pageSize = 50;

  bool isLoadingMore = false;

  bool get hasMore => currentOffset < filteredOptions.length;

  List<Place> _removeDuplicatesByCategory(List<Place> places) {
    final seen = <String>{};
    final result = <Place>[];

    for (final place in places) {
      final category = place.category.trim().toLowerCase();
      final externalId = place.externalId?.trim();

      final key = externalId != null && externalId.isNotEmpty
          ? '$category|external:$externalId'
          : '$category|name:${place.name.trim().toLowerCase()}';

      if (seen.add(key)) {
        result.add(place);
      }
    }

    return result;
  }

  String _placeIdentity(Place place) {
    final externalId = place.externalId?.trim();

    if (externalId != null && externalId.isNotEmpty) {
      return 'external:$externalId';
    }

    return 'name:${place.name.trim().toLowerCase()}'
        '|city:${place.city.trim().toLowerCase()}'
        '|address:${place.address.trim().toLowerCase()}';
  }

  bool _samePlace(Place first, Place second) {
    if (first.latitude != null &&
        first.longitude != null &&
        second.latitude != null &&
        second.longitude != null) {
      return first.latitude == second.latitude &&
          first.longitude == second.longitude;
    }

    final firstExternalId = first.externalId?.trim();
    final secondExternalId = second.externalId?.trim();

    if (firstExternalId != null &&
        firstExternalId.isNotEmpty &&
        secondExternalId != null &&
        secondExternalId.isNotEmpty) {
      return firstExternalId == secondExternalId;
    }

    return first.name.trim().toLowerCase() ==
            second.name.trim().toLowerCase() &&
        first.city.trim().toLowerCase() == second.city.trim().toLowerCase() &&
        first.address.trim().toLowerCase() ==
            second.address.trim().toLowerCase();
  }

  void _initializeSelectedIndexes() {
    selectedIndexes.clear();

    if (!isAddingPlaces) {
      return;
    }

    for (final place in widget.initialSelectedPlaces) {
      selectedPlaceIds.add(_placeIdentity(place));
    }

    for (var index = 0; index < options.length; index++) {
      final place = options[index];

      if (selectedPlaceIds.contains(_placeIdentity(place))) {
        selectedIndexes.add(index);
      }
    }
  }

  Future<void> loadPlaceOptions() async {
    final tripId = widget.trip['id'];

    try {
      setState(() {
        isLoading = true;
        errorMessage = null;
      });

      final categoriesToLoad = selectedCategories.contains('All')
          ? categories.where((category) => category != 'All').toList()
          : selectedCategories.toList();

      final allOptions = <Place>[];

      for (final category in categoriesToLoad) {
        final result = await PlaceService.getPlaceOptions(
          tripId: tripId,
          radiusKm: useRadius ? radiusKm.round() : null,
          searchType: searchType,
          category: category,
          offset: 0,
          limit: 500,
        );

        allOptions.addAll(result.options);
      }

      if (!mounted) return;

      final uniqueOptions = _removeDuplicatesByCategory(allOptions);

      options = uniqueOptions;

      _initializeSelectedIndexes();

      setState(() {
        currentOffset = uniqueOptions.length > pageSize
            ? pageSize
            : uniqueOptions.length;

        isLoading = false;
        isLoadingMore = false;
        errorMessage = null;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        errorMessage = 'Failed to load place options; $e';
        isLoading = false;
        isLoadingMore = false;
      });
    }
  }

  void loadMorePlaceOptions() {
    if (isLoadingMore || !hasMore) return;

    setState(() {
      isLoadingMore = true;

      currentOffset = (currentOffset + pageSize).clamp(
        0,
        filteredOptions.length,
      );

      isLoadingMore = false;
    });
  }

  @override
  void initState() {
    super.initState();

    _scrollController.addListener(_handleScroll);

    nameSearchController.addListener(() {
      if (!mounted) return;

      setState(() {
        nameSearch = nameSearchController.text.trim().toLowerCase();
      });
    });

    loadPlaceOptions();
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) {
      return;
    }

    final shouldShow = _scrollController.offset > 500;

    if (shouldShow != _showScrollToTop) {
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

  @override
  void dispose() {
    _scrollController.removeListener(_handleScroll);
    _scrollController.dispose();

    nameSearchController.dispose();

    super.dispose();
  }

  IconData getPlaceIcon(String category) {
    switch (category) {
      case 'Attractions':
        return Icons.account_balance;

      case 'Nature':
        return Icons.park;

      case 'Entertainment':
        return Icons.movie;

      case 'Food':
        return Icons.restaurant;

      case 'Shopping':
        return Icons.shopping_bag;

      default:
        return Icons.place;
    }
  }

  void togglePlace(int index) {
    if (index < 0 || index >= options.length) {
      return;
    }

    final selectedPlace = options[index];

    final relatedIndexes = <int>[];

    for (var i = 0; i < options.length; i++) {
      if (_samePlace(selectedPlace, options[i])) {
        relatedIndexes.add(i);
      }
    }

    final placeId = _placeIdentity(selectedPlace);
    final isSelected = selectedPlaceIds.contains(placeId);

    setState(() {
      if (isSelected) {
        selectedPlaceIds.remove(placeId);
        selectedIndexes.removeAll(relatedIndexes);
      } else {
        selectedPlaceIds.add(placeId);
        selectedIndexes.addAll(relatedIndexes);
      }
    });
  }

  void togglePlaceFromMap(Place place) {
    final index = options.indexWhere((option) => _samePlace(option, place));

    if (index == -1) {
      return;
    }

    togglePlace(index);
  }

  void savePlaces() {
    final selectedPlaces = selectedIndexes
        .where((index) => index >= 0 && index < options.length)
        .map((index) => options[index])
        .toList();

    if (!isAddingPlaces) {
      Navigator.pop(context, selectedPlaces);
      return;
    }

    final result = <Place>[];

    // Оставляем ранее сохранённые места, которые пользователь
    // не снял с выбора.
    for (final initialPlace in widget.initialSelectedPlaces) {
      final stillSelected = selectedPlaces.any(
        (selectedPlace) => _samePlace(selectedPlace, initialPlace),
      );

      if (stillSelected) {
        result.add(initialPlace);
      }
    }

    // Добавляем все выбранные записи.
    // Разные категории одного физического места сохраняются.
    for (final selectedPlace in selectedPlaces) {
      final alreadyInResult = result.any(
        (place) =>
            place.externalId == selectedPlace.externalId &&
            place.category == selectedPlace.category,
      );

      if (!alreadyInResult) {
        result.add(selectedPlace);
      }
    }

    Navigator.pop(context, result);
  }

  List<Place> get filteredOptions {
    final filteredIndexes = <int>[];

    for (var index = 0; index < options.length; index++) {
      final place = options[index];

      if (!selectedCategories.contains('All')) {
        final selectedCategoryNames = selectedCategories
            .map((category) => category.toLowerCase())
            .toSet();

        if (!selectedCategoryNames.contains(place.category.toLowerCase())) {
          continue;
        }
      }

      // Уже сохранённые места не показываем повторно
      // при режиме Add places.
      if (isAddingPlaces) {
        final alreadySelected = widget.initialSelectedPlaces.any(
          (selectedPlace) => _samePlace(selectedPlace, place),
        );

        if (alreadySelected) {
          continue;
        }
      }

      final nameMatches =
          nameSearch.isEmpty || place.name.toLowerCase().contains(nameSearch);

      final radiusMatches =
          searchType == 'country' ||
          !useRadius ||
          place.distanceKm == null ||
          place.distanceKm! <= radiusKm;

      if (nameMatches && radiusMatches) {
        filteredIndexes.add(index);
      }
    }

    final displayIndexes = <int>[];

    if (selectedCategories.contains('All')) {
      final seenPlaces = <String>{};

      for (final index in filteredIndexes) {
        final place = options[index];
        final identity = _placeIdentity(place);

        if (seenPlaces.add(identity)) {
          displayIndexes.add(index);
        }
      }
    } else {
      displayIndexes.addAll(filteredIndexes);
    }

    // Разделяем места на обычные и выбранные.
    // Выбранные всегда будут внизу списка.
    final selected = displayIndexes
        .where(
          (index) => selectedPlaceIds.contains(_placeIdentity(options[index])),
        )
        .toList();

    final unselected = displayIndexes
        .where(
          (index) => !selectedPlaceIds.contains(_placeIdentity(options[index])),
        )
        .toList();

    int comparePlaces(int a, int b) {
      final placeA = options[a];
      final placeB = options[b];

      switch (selectedSort) {
        case 'Distance':
          final distanceA = placeA.distanceKm ?? double.infinity;
          final distanceB = placeB.distanceKm ?? double.infinity;

          return distanceA.compareTo(distanceB);

        case 'Rating':
          final ratingA = placeA.rating ?? -1;
          final ratingB = placeB.rating ?? -1;

          return ratingB.compareTo(ratingA);

        case 'Name':
          return placeA.name.toLowerCase().compareTo(placeB.name.toLowerCase());

        case 'Significance':
        default:
          // Для Significance сохраняем исходный порядок,
          // который пришёл с backend.
          return a.compareTo(b);
      }
    }

    unselected.sort(comparePlaces);
    selected.sort(comparePlaces);

    // Сначала обычные места, выбранные — в самом низу.
    return [
      ...unselected.map((index) => options[index]),
      ...selected.map((index) => options[index]),
    ];
  }

  List<Place> get visibleOptions {
    final end = currentOffset.clamp(0, filteredOptions.length);

    return filteredOptions.take(end).toList();
  }

  List<Place> get mapPlaces {
    final result = <Place>[];

    // Все текущие места после фильтров.
    for (final place in filteredOptions) {
      if (!result.any((existing) => _samePlace(existing, place))) {
        result.add(place);
      }
    }

    // Уже сохранённые места тоже обязательно оставляем на карте.
    // Они могут быть исключены из списка.
    for (final place in widget.initialSelectedPlaces) {
      if (!result.any((existing) => _samePlace(existing, place))) {
        result.add(place);
      }
    }

    return result;
  }

  List<Place> get mapSelectedPlaces {
    final result = <Place>[];

    // Уже сохранённые места.
    for (final place in widget.initialSelectedPlaces) {
      if (!result.any((existing) => _samePlace(existing, place))) {
        result.add(place);
      }
    }

    // Текущий выбор.
    for (final index in selectedIndexes) {
      if (index < 0 || index >= options.length) {
        continue;
      }

      final place = options[index];

      if (!result.any((existing) => _samePlace(existing, place))) {
        result.add(place);
      }
    }

    // Если пользователь снял выбор с ранее сохранённого места,
    // оно больше не должно оставаться синим.
    if (isAddingPlaces) {
      result.removeWhere((selectedPlace) {
        final index = options.indexWhere(
          (option) => _samePlace(option, selectedPlace),
        );

        if (index == -1) {
          return false;
        }

        return !selectedIndexes.contains(index);
      });
    }

    return result;
  }

  void clearFilters() {
    setState(() {
      selectedCategories = {'All'};
      selectedSort = 'Significance';
      searchType = 'city';

      useRadius = false;
      radiusKm = 5;

      nameSearchController.clear();

      currentOffset = 0;

      isLoading = true;
      errorMessage = null;
    });

    loadPlaceOptions();
  }

  Widget buildCardView() {
    final filtered = visibleOptions;

    if (filtered.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 40),
        child: Center(
          child: Text(
            'No places match the selected filters.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16),
          ),
        ),
      );
    }

    return Column(
      children: filtered.map((option) {
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
                      color: Colors.blue.withValues(alpha: 0.1),
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
                            Flexible(
                              child: Text(
                                option.category,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.grey.shade700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 3),
                        Text(
                          [
                            if (option.city.isNotEmpty) option.city,
                            if (option.country != null &&
                                option.country!.isNotEmpty)
                              option.country!,
                          ].join(', '),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
                        ),
                        const SizedBox(height: 2),
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
                            if (option.distanceKm != null) ...[
                              const Icon(
                                Icons.near_me,
                                size: 15,
                                color: Colors.grey,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${option.distanceKm!.toStringAsFixed(1)} km',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey.shade700,
                                ),
                              ),
                            ],
                            const SizedBox(width: 12),
                            const Icon(
                              Icons.star,
                              size: 15,
                              color: Colors.amber,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              option.rating != null
                                  ? option.rating!.toStringAsFixed(1)
                                  : '—',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade700,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            Text(
                              option.openingTime != null &&
                                      option.closingTime != null
                                  ? '${option.openingTime}–${option.closingTime}'
                                  : 'Opening hours unavailable',
                              style: const TextStyle(fontSize: 12),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              'Visit: ${option.visitDuration ?? '-'}',
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
                    onChanged: (_) {
                      togglePlace(originalIndex);
                    },
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
    final filtered = visibleOptions;

    if (filtered.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 40),
        child: Center(
          child: Text(
            'No places match the selected filters.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16),
          ),
        ),
      );
    }

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: filtered.map((option) {
          final originalIndex = options.indexOf(option);
          final isSelected = selectedIndexes.contains(originalIndex);

          final locationText = [
            if (option.city.isNotEmpty) option.city,
            if (option.country != null && option.country!.isNotEmpty)
              option.country!,
          ].join(', ');

          return ListTile(
            leading: Icon(getPlaceIcon(option.category), color: Colors.blue),
            title: Text(
              option.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              [
                option.category,
                if (locationText.isNotEmpty) locationText,
                option.address,
              ].join(' • '),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: Checkbox(
              value: isSelected,
              onChanged: (_) {
                togglePlace(originalIndex);
              },
            ),
            onTap: () {
              togglePlace(originalIndex);
            },
          );
        }).toList(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final destination = widget.trip['destination'];

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Places to Visit',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: _buildBody(destination),
      floatingActionButton: _showScrollToTop
          ? FloatingActionButton(
              onPressed: _scrollToTop,
              child: const Icon(Icons.keyboard_arrow_up),
            )
          : null,
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
                          ? 'Save Places'
                          : 'Save Places (${selectedIndexes.length})',
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
      controller: _scrollController,
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

          if (searchType == 'city') ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Distance limit',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                Switch(
                  value: useRadius,
                  onChanged: (value) {
                    setState(() {
                      useRadius = value;
                    });

                    loadPlaceOptions();
                  },
                ),
              ],
            ),
          ],

          if (searchType == 'city' && useRadius) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Maximum distance'),
                Text(
                  '${radiusKm.round()} km',
                  style: const TextStyle(fontWeight: FontWeight.bold),
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
              onChangeEnd: (_) {
                loadPlaceOptions();
              },
            ),
          ],

          const SizedBox(height: 12),

          TextField(
            controller: nameSearchController,
            decoration: InputDecoration(
              labelText: 'Search by name',
              hintText: 'Enter place name',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: nameSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        nameSearchController.clear();
                      },
                    )
                  : null,
              border: const OutlineInputBorder(),
            ),
          ),

          const SizedBox(height: 12),

          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Search area',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment<String>(
                    value: 'city',
                    label: Text('City'),
                    icon: Icon(Icons.location_city),
                  ),
                  ButtonSegment<String>(
                    value: 'country',
                    label: Text('Country'),
                    icon: Icon(Icons.public),
                  ),
                ],
                selected: {searchType},
                onSelectionChanged: (selection) {
                  setState(() {
                    searchType = selection.first;
                    options = [];
                    currentOffset = 0;
                    isLoading = true;
                    errorMessage = null;
                  });

                  loadPlaceOptions();
                },
              ),
            ],
          ),

          const SizedBox(height: 12),

          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: clearFilters,
              icon: const Icon(Icons.clear_all),
              label: const Text('Clear filters'),
            ),
          ),

          const SizedBox(height: 4),

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

          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: categories.map((category) {
              final isSelected = selectedCategories.contains(category);

              return FilterChip(
                label: Text(category),
                selected: isSelected,
                onSelected: (_) {
                  setState(() {
                    if (category == 'All') {
                      selectedCategories = {'All'};
                    } else {
                      selectedCategories.remove('All');

                      if (selectedCategories.contains(category)) {
                        selectedCategories.remove(category);
                      } else {
                        selectedCategories.add(category);
                      }

                      if (selectedCategories.isEmpty) {
                        selectedCategories = {'All'};
                      }
                    }

                    currentOffset = 0;
                    options = [];
                    isLoading = true;
                    errorMessage = null;
                  });

                  loadPlaceOptions();
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 14),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Sort by',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              DropdownButton<String>(
                value: selectedSort,
                items: const [
                  DropdownMenuItem(
                    value: 'Significance',
                    child: Text('Significance'),
                  ),
                  DropdownMenuItem(value: 'Name', child: Text('Name')),
                  DropdownMenuItem(value: 'Distance', child: Text('Distance')),
                  DropdownMenuItem(value: 'Rating', child: Text('Rating')),
                ],
                onChanged: (value) {
                  if (value == null) return;

                  setState(() {
                    selectedSort = value;
                  });
                },
              ),
            ],
          ),

          const SizedBox(height: 12),

          Text(
            '${filteredOptions.length} places found',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),

          const SizedBox(height: 10),

          PlacesMap(
            places: mapPlaces,
            selectedPlaces: mapSelectedPlaces,
            onPlaceTap: togglePlaceFromMap,
          ),

          const SizedBox(height: 16),

          isListView ? buildListView() : buildCardView(),

          if (hasMore && visibleOptions.isNotEmpty) ...[
            const SizedBox(height: 16),
            Center(
              child: isLoadingMore
                  ? const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: CircularProgressIndicator(),
                    )
                  : ElevatedButton(
                      onPressed: loadMorePlaceOptions,
                      child: const Text('Load more'),
                    ),
            ),
          ],
        ],
      ),
    );
  }
}
