package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(k = 3, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
final class ScreensKt$LoginScreen$1$1 implements kotlin.jvm.functions.Function3<androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, java.lang.Integer, kotlin.Unit> {
    final /* synthetic */ com.ctf.loi.LocalDbHelper $dbHelper;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $info$delegate;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $name$delegate;
    final /* synthetic */ kotlin.jvm.functions.Function0<kotlin.Unit> $onBack;
    final /* synthetic */ kotlin.jvm.functions.Function1<java.lang.String, kotlin.Unit> $onLoginFailure;
    final /* synthetic */ kotlin.jvm.functions.Function1<com.ctf.loi.UserRow, kotlin.Unit> $onLoginSuccess;

    /* JADX WARN: Multi-variable type inference failed */
    ScreensKt$LoginScreen$1$1(androidx.compose.runtime.MutableState<java.lang.String> mutableState, kotlin.jvm.functions.Function0<kotlin.Unit> function0, com.ctf.loi.LocalDbHelper localDbHelper, kotlin.jvm.functions.Function1<? super java.lang.String, kotlin.Unit> function1, kotlin.jvm.functions.Function1<? super com.ctf.loi.UserRow, kotlin.Unit> function12, androidx.compose.runtime.MutableState<java.lang.String> mutableState2) {
        this.$name$delegate = mutableState;
        this.$onBack = function0;
        this.$dbHelper = localDbHelper;
        this.$onLoginFailure = function1;
        this.$onLoginSuccess = function12;
        this.$info$delegate = mutableState2;
    }

    @Override // kotlin.jvm.functions.Function3
    public /* bridge */ /* synthetic */ kotlin.Unit invoke(androidx.compose.foundation.layout.ColumnScope columnScope, androidx.compose.runtime.Composer composer, java.lang.Integer num) {
        invoke(columnScope, composer, num.intValue());
        return kotlin.Unit.INSTANCE;
    }

    /* JADX WARN: Removed duplicated region for block: B:24:0x0211  */
    /* JADX WARN: Removed duplicated region for block: B:27:0x02ea  */
    /* JADX WARN: Removed duplicated region for block: B:30:0x02f6  */
    /* JADX WARN: Removed duplicated region for block: B:38:0x03fd  */
    /* JADX WARN: Removed duplicated region for block: B:43:0x04d4  */
    /* JADX WARN: Removed duplicated region for block: B:45:? A[RETURN, SYNTHETIC] */
    /* JADX WARN: Removed duplicated region for block: B:49:0x02fa  */
    /* JADX WARN: Removed duplicated region for block: B:50:0x021f  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
        To view partially-correct add '--show-bad-code' argument
    */
    public final void invoke(androidx.compose.foundation.layout.ColumnScope r74, androidx.compose.runtime.Composer r75, int r76) {
        /*
            Method dump skipped, instructions count: 1240
            To view this dump add '--comments-level debug' option
        */
        throw new UnsupportedOperationException("Method not decompiled: com.ctf.loi.ScreensKt$LoginScreen$1$1.invoke(androidx.compose.foundation.layout.ColumnScope, androidx.compose.runtime.Composer, int):void");
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$5$lambda$1$lambda$0(androidx.compose.runtime.MutableState $name$delegate, java.lang.String it) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(it, "it");
        $name$delegate.setValue(it);
        return kotlin.Unit.INSTANCE;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public static final kotlin.Unit invoke$lambda$5$lambda$4$lambda$3$lambda$2(com.ctf.loi.LocalDbHelper $dbHelper, kotlin.jvm.functions.Function1 $onLoginFailure, kotlin.jvm.functions.Function1 $onLoginSuccess, androidx.compose.runtime.MutableState $name$delegate, androidx.compose.runtime.MutableState $info$delegate) {
        java.lang.String LoginScreen$lambda$42;
        java.lang.String LoginScreen$lambda$45;
        java.lang.String LoginScreen$lambda$452;
        LoginScreen$lambda$42 = com.ctf.loi.ScreensKt.LoginScreen$lambda$42($name$delegate);
        com.ctf.loi.UserRow user = $dbHelper.safeFindByName(kotlin.text.StringsKt.trim((java.lang.CharSequence) LoginScreen$lambda$42).toString());
        if (user != null) {
            if (user.isAdmin() == 1) {
                $onLoginSuccess.invoke(user);
            } else {
                $info$delegate.setValue("Welcome, " + user.getName() + ", you dont have the admin role.");
                LoginScreen$lambda$45 = com.ctf.loi.ScreensKt.LoginScreen$lambda$45($info$delegate);
                $onLoginFailure.invoke(LoginScreen$lambda$45);
            }
        } else {
            $info$delegate.setValue("No user found.");
            LoginScreen$lambda$452 = com.ctf.loi.ScreensKt.LoginScreen$lambda$45($info$delegate);
            $onLoginFailure.invoke(LoginScreen$lambda$452);
        }
        return kotlin.Unit.INSTANCE;
    }
}
