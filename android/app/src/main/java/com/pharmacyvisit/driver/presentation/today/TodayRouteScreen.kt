package com.pharmacyvisit.driver.presentation.today

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class FakeStop(
    val id: String,
    val order: Int,
    val name: String,
    val address: String,
    val status: String
)

val sampleStops = listOf(
    FakeStop("1", 1, "داروخانه دکتر رضایی", "تهران، خیابان ولیعصر، پلاک ۲۳۰", "در انتظار"),
    FakeStop("2", 2, "داروخانه شبانه روزی آریا", "تهران، سعادت آباد، میدان کاج", "در انتظار"),
    FakeStop("3", 3, "داروخانه مرکزی انقلاب", "تهران، خیابان انقلاب، روبروی دانشگاه", "در انتظار"),
    FakeStop("4", 4, "داروخانه دکتر محمدی", "تهران، پونک، بلوار میرزا بابایی", "در انتظار"),
    FakeStop("5", 5, "داروخانه فردوسی", "تهران، خیابان فردوسی، بالاتر از جمهوری", "در انتظار")
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TodayRouteScreen(
    onStopClick: (String) -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("مسیر امروز") }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Summary card
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("۵ توقف باقی‌مانده", style = MaterialTheme.typography.titleMedium)
                    Text("زمان تقریبی کل: ۴ ساعت و ۲۰ دقیقه", style = MaterialTheme.typography.bodyMedium)
                }
            }

            LazyColumn(
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(sampleStops) { stop ->
                    StopCard(stop = stop, onClick = { onStopClick(stop.id) })
                }
            }
        }
    }
}

@Composable
fun StopCard(
    stop: FakeStop,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                shape = MaterialTheme.shapes.small,
                color = MaterialTheme.colorScheme.primaryContainer,
                modifier = Modifier.size(40.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = stop.order.toString(),
                        style = MaterialTheme.typography.titleMedium
                    )
                }
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(stop.name, style = MaterialTheme.typography.titleMedium)
                Text(stop.address, style = MaterialTheme.typography.bodySmall)
                Text(stop.status, style = MaterialTheme.typography.labelMedium)
            }
        }
    }
}
