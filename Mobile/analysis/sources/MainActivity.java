package com.ctf.loi;

/* compiled from: MainActivity.kt */
@kotlin.Metadata(d1 = {"\u0000,\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\u0010\u0011\n\u0002\u0010\u000e\n\u0000\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u0007¢\u0006\u0004\b\u0002\u0010\u0003J\u0012\u0010\n\u001a\u00020\u000b2\b\u0010\f\u001a\u0004\u0018\u00010\rH\u0014R\u000e\u0010\u0004\u001a\u00020\u0005X\u0082.¢\u0006\u0002\n\u0000R\u001a\u0010\u0006\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\t0\b0\u0007X\u0082\u0004¢\u0006\u0002\n\u0000¨\u0006\u000e"}, d2 = {"Lcom/ctf/loi/MainActivity;", "Landroidx/activity/ComponentActivity;", "<init>", "()V", "dbHelper", "Lcom/ctf/loi/LocalDbHelper;", "permissionLauncher", "Landroidx/activity/result/ActivityResultLauncher;", "", "", "onCreate", "", "savedInstanceState", "Landroid/os/Bundle;", "app_debug"}, k = 1, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
public final class MainActivity extends androidx.activity.ComponentActivity {
    public static final int $stable = 8;
    private com.ctf.loi.LocalDbHelper dbHelper;
    private final androidx.activity.result.ActivityResultLauncher<java.lang.String[]> permissionLauncher = registerForActivityResult(new androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions(), new androidx.activity.result.ActivityResultCallback() { // from class: com.ctf.loi.MainActivity$$ExternalSyntheticLambda0
        @Override // androidx.activity.result.ActivityResultCallback
        public final void onActivityResult(java.lang.Object obj) {
            kotlin.jvm.internal.Intrinsics.checkNotNullParameter((java.util.Map) obj, "it");
        }
    });

    /* JADX WARN: Multi-variable type inference failed */
    @Override // androidx.activity.ComponentActivity, androidx.core.app.ComponentActivity, android.app.Activity
    protected void onCreate(android.os.Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        androidx.activity.EdgeToEdge.enable$default(this, null, null, 3, null);
        this.dbHelper = new com.ctf.loi.LocalDbHelper(this);
        java.lang.String string = getResources().getString(com.ctf.loi.R.string.l1);
        kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(string, "getString(...)");
        final double allowedLat = java.lang.Double.parseDouble(string);
        java.lang.String string2 = getResources().getString(com.ctf.loi.R.string.l2);
        kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(string2, "getString(...)");
        final double allowedLon = java.lang.Double.parseDouble(string2);
        java.lang.String string3 = getResources().getString(com.ctf.loi.R.string.al_r);
        kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(string3, "getString(...)");
        final double allowedRadius = java.lang.Double.parseDouble(string3);
        androidx.activity.compose.ComponentActivityKt.setContent$default(this, null, androidx.compose.runtime.internal.ComposableLambdaKt.composableLambdaInstance(-1622795688, true, new kotlin.jvm.functions.Function2<androidx.compose.runtime.Composer, java.lang.Integer, kotlin.Unit>() { // from class: com.ctf.loi.MainActivity$onCreate$1
            @Override // kotlin.jvm.functions.Function2
            public /* bridge */ /* synthetic */ kotlin.Unit invoke(androidx.compose.runtime.Composer composer, java.lang.Integer num) {
                invoke(composer, num.intValue());
                return kotlin.Unit.INSTANCE;
            }

            public final void invoke(androidx.compose.runtime.Composer $composer, int $changed) {
                com.ctf.loi.LocalDbHelper localDbHelper;
                androidx.compose.runtime.ComposerKt.sourceInformation($composer, "C30@1005L62:MainActivity.kt#w10jgg");
                if (($changed & 3) != 2 || !$composer.getSkipping()) {
                    if (androidx.compose.runtime.ComposerKt.isTraceInProgress()) {
                        androidx.compose.runtime.ComposerKt.traceEventStart(-1622795688, $changed, -1, "com.ctf.loi.MainActivity.onCreate.<anonymous> (MainActivity.kt:30)");
                    }
                    localDbHelper = com.ctf.loi.MainActivity.this.dbHelper;
                    if (localDbHelper == null) {
                        kotlin.jvm.internal.Intrinsics.throwUninitializedPropertyAccessException("dbHelper");
                        localDbHelper = null;
                    }
                    com.ctf.loi.ScreensKt.AppRoot(localDbHelper, com.ctf.loi.MainActivity.this, allowedLat, allowedLon, allowedRadius, $composer, 0);
                    if (androidx.compose.runtime.ComposerKt.isTraceInProgress()) {
                        androidx.compose.runtime.ComposerKt.traceEventEnd();
                        return;
                    }
                    return;
                }
                $composer.skipToGroupEnd();
            }
        }), 1, null);
        java.util.List needed = new java.util.ArrayList();
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, "android.permission.ACCESS_COARSE_LOCATION") != 0) {
            needed.add("android.permission.ACCESS_COARSE_LOCATION");
        }
        if (androidx.core.content.ContextCompat.checkSelfPermission(this, "android.permission.ACCESS_FINE_LOCATION") != 0) {
            needed.add("android.permission.ACCESS_FINE_LOCATION");
        }
        if (!needed.isEmpty()) {
            this.permissionLauncher.launch(needed.toArray(new java.lang.String[0]));
        }
    }
}
