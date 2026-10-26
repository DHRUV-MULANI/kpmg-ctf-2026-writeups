package com.ctf.loi;

/* compiled from: Utils.kt */
@kotlin.Metadata(d1 = {"\u0000 \n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u0006\n\u0002\b\u0005\bÇ\u0002\u0018\u00002\u00020\u0001B\t\b\u0002¢\u0006\u0004\b\u0002\u0010\u0003J\u0010\u0010\u0004\u001a\u0004\u0018\u00010\u00052\u0006\u0010\u0006\u001a\u00020\u0007J&\u0010\b\u001a\u00020\t2\u0006\u0010\n\u001a\u00020\t2\u0006\u0010\u000b\u001a\u00020\t2\u0006\u0010\f\u001a\u00020\t2\u0006\u0010\r\u001a\u00020\t¨\u0006\u000e"}, d2 = {"Lcom/ctf/loi/Utils;", "", "<init>", "()V", "getLastKnownLocation", "Landroid/location/Location;", "ctx", "Landroid/content/Context;", "distanceMeters", "", "lat1", "lon1", "lat2", "lon2", "app_debug"}, k = 1, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
public final class Utils {
    public static final int $stable = 0;
    public static final com.ctf.loi.Utils INSTANCE = new com.ctf.loi.Utils();

    private Utils() {
    }

    public final android.location.Location getLastKnownLocation(android.content.Context ctx) {
        android.location.Location l;
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(ctx, "ctx");
        java.lang.Object systemService = ctx.getSystemService("location");
        kotlin.jvm.internal.Intrinsics.checkNotNull(systemService, "null cannot be cast to non-null type android.location.LocationManager");
        android.location.LocationManager lm = (android.location.LocationManager) systemService;
        java.util.List providers = lm.getProviders(true);
        kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(providers, "getProviders(...)");
        for (java.lang.String p : providers) {
            try {
                l = lm.getLastKnownLocation(p);
            } catch (java.lang.SecurityException e) {
            }
            if (l != null) {
                return l;
            }
        }
        return null;
    }

    public final double distanceMeters(double lat1, double lon1, double lat2, double lon2) {
        double dLat = java.lang.Math.toRadians(lat2 - lat1);
        double dLon = java.lang.Math.toRadians(lon2 - lon1);
        double d = 2;
        double a = (java.lang.Math.sin(dLat / d) * java.lang.Math.sin(dLat / d)) + (java.lang.Math.cos(java.lang.Math.toRadians(lat1)) * java.lang.Math.cos(java.lang.Math.toRadians(lat2)) * java.lang.Math.sin(dLon / d) * java.lang.Math.sin(dLon / d));
        double c = d * java.lang.Math.atan2(java.lang.Math.sqrt(a), java.lang.Math.sqrt(1 - a));
        return 6371000.0d * c;
    }
}
