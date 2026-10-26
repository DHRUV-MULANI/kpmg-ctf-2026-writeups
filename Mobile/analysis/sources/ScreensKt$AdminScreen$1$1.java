package com.ctf.loi;

/* compiled from: Screens.kt */
@kotlin.Metadata(d1 = {"\u0000\n\n\u0000\n\u0002\u0010\u0002\n\u0002\u0018\u0002\u0010\u0000\u001a\u00020\u0001*\u00020\u0002H\n"}, d2 = {"<anonymous>", "", "Lkotlinx/coroutines/CoroutineScope;"}, k = 3, mv = {2, 0, 0}, xi = 48)
@kotlin.coroutines.jvm.internal.DebugMetadata(c = "com.ctf.loi.ScreensKt$AdminScreen$1$1", f = "Screens.kt", i = {}, l = {350}, m = "invokeSuspend", n = {}, s = {})
/* loaded from: classes4.dex */
final class ScreensKt$AdminScreen$1$1 extends kotlin.coroutines.jvm.internal.SuspendLambda implements kotlin.jvm.functions.Function2<kotlinx.coroutines.CoroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit>, java.lang.Object> {
    final /* synthetic */ java.lang.String $PLACEHOLDER_EMAIL;
    final /* synthetic */ java.lang.String $PLACEHOLDER_NAME;
    final /* synthetic */ com.ctf.loi.UserRow $adminUser;
    final /* synthetic */ android.content.Context $ctx;
    final /* synthetic */ com.ctf.loi.LocalDbHelper $dbHelper;
    final /* synthetic */ androidx.compose.runtime.MutableState<java.lang.String> $privilegedInfo$delegate;
    int label;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    ScreensKt$AdminScreen$1$1(com.ctf.loi.UserRow userRow, android.content.Context context, androidx.compose.runtime.MutableState<java.lang.String> mutableState, com.ctf.loi.LocalDbHelper localDbHelper, java.lang.String str, java.lang.String str2, kotlin.coroutines.Continuation<? super com.ctf.loi.ScreensKt$AdminScreen$1$1> continuation) {
        super(2, continuation);
        this.$adminUser = userRow;
        this.$ctx = context;
        this.$privilegedInfo$delegate = mutableState;
        this.$dbHelper = localDbHelper;
        this.$PLACEHOLDER_NAME = str;
        this.$PLACEHOLDER_EMAIL = str2;
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final kotlin.coroutines.Continuation<kotlin.Unit> create(java.lang.Object obj, kotlin.coroutines.Continuation<?> continuation) {
        return new com.ctf.loi.ScreensKt$AdminScreen$1$1(this.$adminUser, this.$ctx, this.$privilegedInfo$delegate, this.$dbHelper, this.$PLACEHOLDER_NAME, this.$PLACEHOLDER_EMAIL, continuation);
    }

    @Override // kotlin.jvm.functions.Function2
    public final java.lang.Object invoke(kotlinx.coroutines.CoroutineScope coroutineScope, kotlin.coroutines.Continuation<? super kotlin.Unit> continuation) {
        return ((com.ctf.loi.ScreensKt$AdminScreen$1$1) create(coroutineScope, continuation)).invokeSuspend(kotlin.Unit.INSTANCE);
    }

    @Override // kotlin.coroutines.jvm.internal.BaseContinuationImpl
    public final java.lang.Object invokeSuspend(java.lang.Object $result) {
        java.lang.Object coroutine_suspended = kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED();
        switch (this.label) {
            case 0:
                kotlin.ResultKt.throwOnFailure($result);
                if (this.$adminUser == null || this.$adminUser.isAdmin() != 1) {
                    this.label = 1;
                    java.lang.Object withContext = kotlinx.coroutines.BuildersKt.withContext(kotlinx.coroutines.Dispatchers.getIO(), new com.ctf.loi.ScreensKt$AdminScreen$1$1$adminEmail$1(this.$dbHelper, this.$PLACEHOLDER_NAME, this.$PLACEHOLDER_EMAIL, null), this);
                    if (withContext != coroutine_suspended) {
                        $result = withContext;
                        break;
                    } else {
                        return coroutine_suspended;
                    }
                } else {
                    this.$privilegedInfo$delegate.setValue(this.$ctx.getString(com.ctf.loi.R.string.not_required7));
                    return kotlin.Unit.INSTANCE;
                }
            case 1:
                kotlin.ResultKt.throwOnFailure($result);
                break;
            default:
                throw new java.lang.IllegalStateException("call to 'resume' before 'invoke' with coroutine");
        }
        java.lang.String adminEmail = (java.lang.String) $result;
        androidx.compose.runtime.MutableState<java.lang.String> mutableState = this.$privilegedInfo$delegate;
        if (adminEmail == null) {
            adminEmail = "No privileged info found.";
        }
        mutableState.setValue(adminEmail);
        return kotlin.Unit.INSTANCE;
    }
}
