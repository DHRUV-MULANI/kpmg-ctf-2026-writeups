package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
final class ScreensKt$HomeScreen$2$1 implements kotlin.jvm.functions.Function3<androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, java.lang.Integer, kotlin.Unit> {
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.Boolean> $allowed$delegate;
    final /* synthetic */ double $allowedLat;
    final /* synthetic */ double $allowedLon;
    final /* synthetic */ double $allowedRadius;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.Boolean> $checking$delegate;
    final /* synthetic */ androidx.activity.ComponentActivity $context;
    final /* synthetic */ com.google.android.gms.location.FusedLocationProviderClient $fusedClient;
    final /* synthetic */ kotlin.jvm.functions.Function1<java.lang.String, kotlin.Unit> $onMessage;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $status$delegate;

    /* JADX WARN: Multi-variable type inference failed */
    ScreensKt$HomeScreen$2$1(androidx.compose.runtime.MutableState<java.lang.Boolean> mutableState, androidx.compose.runtime.MutableState<java.lang.String> mutableState2, androidx.compose.runtime.MutableState<java.lang.Boolean> mutableState3, kotlin.jvm.functions.Function1<? super java.lang.String, kotlin.Unit> function1, androidx.activity.ComponentActivity componentActivity, com.google.android.gms.location.FusedLocationProviderClient fusedLocationProviderClient, double d, double d2, double d3) {
        this.$checking$delegate = mutableState;
        this.$status$delegate = mutableState2;
        this.$allowed$delegate = mutableState3;
        this.$onMessage = function1;
        this.$context = componentActivity;
        this.$fusedClient = fusedLocationProviderClient;
        this.$allowedLat = d;
        this.$allowedLon = d2;
        this.$allowedRadius = d3;
    }

    @Override // kotlin.jvm.functions.Function3
    public /* bridge */ /* synthetic */ kotlin.Unit invoke(androidx.compose.foundation.layout.ColumnScope columnScope, androidx.compose.runtime.Composer composer, java.lang.Integer num) {
        invoke(columnScope, composer, num.intValue());
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:24:0x01ce  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x03f2  */
    /* JADX WARN: Removed duplicated region for block: B:59:0x05f1  */
    /* JADX WARN: Removed duplicated region for block: B:61:? A[RETURN, SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:71:0x037f  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct add '--show-bad-code' argument
    */
    public final void invoke(androidx.compose.foundation.layout.ColumnScope r98, androidx.compose.runtime.Composer r99, int r100) {
        /*
            Method dump skipped, instructions count: 1525
            To view this dump add '--comments-level debug' option
        */
        throw new UnsupportedOperationException("Method not decompiled: com.ctf.loi.ScreensKt$HomeScreen$2$1.invoke(androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, int):void");
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$4$lambda$3$lambda$2$lambda$1(kotlin.jvm.functions.Function1 $onMessage, com.google.android.gms.location.FusedLocationProviderClient $fusedClient, androidx.compose.runtime.MutableState $checking$delegate, androidx.compose.runtime.MutableState $allowed$delegate, androidx.compose.runtime.MutableState $status$delegate, androidx.activity.ComponentActivity $context, double $allowedLat, double $allowedLon, double $allowedRadius) {
        com.ctf.loi.ScreensKt.HomeScreen$fetchFreshLocationThenUpdateUI($onMessage, $fusedClient, $checking$delegate, $allowed$delegate, $status$delegate, $context, $allowedLat, $allowedLon, $allowedRadius);
        return kotlin.Unit.INSTANCE;
    }
}
