package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u000e\n\u0002\u0018\u0002\u0010\u0000\u001a\u0004\u0018\u00010\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.ctf.loi.ScreensKt$AdminScreen$1$1$adminEmail$1", f = "Screens.kt", i = {}, l = {}, m = "invokeSuspend", n = {}, s = {})
/* loaded from: classes4.dex */
final class ScreensKt$AdminScreen$1$1$adminEmail$1 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<kotlinx.coroutines.CoroutineScope, kotlin.coroutines.Continuation<? super java.lang.String>, java.lang.Object> {
    final /* synthetic */ java.lang.String $PLACEHOLDER_EMAIL;
    final /* synthetic */ java.lang.String $PLACEHOLDER_NAME;
    final /* synthetic */ com.ctf.loi.LocalDbHelper $dbHelper;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    ScreensKt$AdminScreen$1$1$adminEmail$1(com.ctf.loi.LocalDbHelper localDbHelper, java.lang.String str, java.lang.String str2, kotlin.coroutines.Continuation<? super com.ctf.loi.ScreensKt$AdminScreen$1$1$adminEmail$1> continuation) {
        super(2, continuation);
        this.$dbHelper = localDbHelper;
        this.$PLACEHOLDER_NAME = str;
        this.$PLACEHOLDER_EMAIL = str2;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
        return new com.ctf.loi.ScreensKt$AdminScreen$1$1$adminEmail$1(this.$dbHelper, this.$PLACEHOLDER_NAME, this.$PLACEHOLDER_EMAIL, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final java.lang.Object invoke(kotlinx.coroutines.CoroutineScope coroutineScope, kotlin.coroutines.Continuation<? super java.lang.String> continuation) {
        return ((com.ctf.loi.ScreensKt$AdminScreen$1$1$adminEmail$1) create(coroutineScope, continuation)).invokeSuspend(kotlin.Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final java.lang.Object invokeSuspend(java.lang.Object obj) {
        java.lang.String str;
        kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (this.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure(obj);
                try {
                    android.database.Cursor readableDatabase = this.$dbHelper.getReadableDatabase();
                    java.lang.String str2 = this.$PLACEHOLDER_NAME;
                    java.lang.String str3 = this.$PLACEHOLDER_EMAIL;
                    try {
                        readableDatabase = readableDatabase.rawQuery("SELECT name, email FROM users WHERE is_admin = 1", null);
                        try {
                            android.database.Cursor cursor = readableDatabase;
                            if (cursor.moveToFirst()) {
                                java.lang.String string = cursor.getString(cursor.getColumnIndexOrThrow(androidx.autofill.HintConstants.AUTOFILL_HINT_NAME));
                                str = cursor.getString(cursor.getColumnIndexOrThrow("email"));
                                if (kotlin.jvm.internal.Intrinsics.areEqual(string, str2)) {
                                    if (kotlin.jvm.internal.Intrinsics.areEqual(str, str3)) {
                                        str = null;
                                    }
                                }
                            } else {
                                str = null;
                            }
                            kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                            kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                            return str;
                        } finally {
                        }
                    } finally {
                    }
                } catch (java.lang.Exception e) {
                    android.util.Log.e("AdminScreen", "error fetching admin: " + e.getMessage());
                    return null;
                }
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
    }
}
