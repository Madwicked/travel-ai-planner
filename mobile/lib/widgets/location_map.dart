import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

class LocationMap extends StatelessWidget {
  final double latitude;
  final double longitude;
  final String title;

  const LocationMap({
    super.key,
    required this.latitude,
    required this.longitude,
    required this.title,
  });

  @override
  Widget build(BuildContext context) {
    final point = LatLng(latitude, longitude);
    final mapController = MapController();

    return SizedBox(
      height: 250,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            FlutterMap(
              mapController: mapController,
              options: MapOptions(initialCenter: point, initialZoom: 15),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.example.travel_ai_planner',
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: point,
                      width: 50,
                      height: 50,
                      child: const Icon(
                        Icons.location_pin,
                        size: 45,
                        color: Colors.red,
                      ),
                    ),
                  ],
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
                      onTap: () => mapController.move(
                        mapController.camera.center,
                        mapController.camera.zoom + 1,
                      ),
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
                      onTap: () => mapController.move(
                        mapController.camera.center,
                        mapController.camera.zoom - 1,
                      ),
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
