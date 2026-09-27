import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../models/place.dart';

class PlacesMap extends StatefulWidget {
  final List<Place> places;
  final List<Place> selectedPlaces;
  final ValueChanged<Place> onPlaceTap;

  const PlacesMap({
    super.key,
    required this.places,
    required this.selectedPlaces,
    required this.onPlaceTap,
  });

  @override
  State<PlacesMap> createState() => _PlacesMapState();
}

class _PlacesMapState extends State<PlacesMap> {
  final MapController _mapController = MapController();

  bool _isSelected(Place place) {
    return widget.selectedPlaces.any(
      (selected) =>
          (selected.externalId != null &&
              place.externalId != null &&
              selected.externalId == place.externalId) ||
          (selected.externalId == null &&
              place.externalId == null &&
              selected.name == place.name &&
              selected.city == place.city &&
              selected.address == place.address),
    );
  }

  @override
  Widget build(BuildContext context) {
    final placesWithCoordinates = widget.places
        .where((place) => place.latitude != null && place.longitude != null)
        .toList();

    if (placesWithCoordinates.isEmpty) {
      return const SizedBox.shrink();
    }

    final firstPlace = placesWithCoordinates.first;

    final center = LatLng(firstPlace.latitude!, firstPlace.longitude!);

    return SizedBox(
      height: 300,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            FlutterMap(
              mapController: _mapController,
              options: MapOptions(initialCenter: center, initialZoom: 12),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.travel_ai_planner',
                ),
                MarkerLayer(
                  markers: placesWithCoordinates.map((place) {
                    final selected = _isSelected(place);

                    return Marker(
                      point: LatLng(place.latitude!, place.longitude!),
                      width: 48,
                      height: 48,
                      child: GestureDetector(
                        onTap: () => widget.onPlaceTap(place),
                        child: Icon(
                          Icons.location_pin,
                          size: 42,
                          color: selected
                              ? Colors.blue
                              : Colors.red.withValues(alpha: 0.25),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),

            Positioned(
              right: 12,
              bottom: 12,
              child: Column(
                children: [
                  Material(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    elevation: 3,
                    child: InkWell(
                      onTap: () {
                        _mapController.move(
                          _mapController.camera.center,
                          _mapController.camera.zoom + 1,
                        );
                      },
                      child: const SizedBox(
                        width: 44,
                        height: 44,
                        child: Icon(Icons.add),
                      ),
                    ),
                  ),
                  const SizedBox(height: 6),
                  Material(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    elevation: 3,
                    child: InkWell(
                      onTap: () {
                        _mapController.move(
                          _mapController.camera.center,
                          _mapController.camera.zoom - 1,
                        );
                      },
                      child: const SizedBox(
                        width: 44,
                        height: 44,
                        child: Icon(Icons.remove),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
