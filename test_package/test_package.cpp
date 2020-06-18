#include <LexFloatClient.h>
#include <stdlib.h>

int main() {
#if _WIN32
	int status = SetHostProductId(L"foo");
#else
	int status = SetHostProductId("bar");
#endif
	if (LF_OK == status)
	{
		return EXIT_FAILURE;
	}
    return EXIT_SUCCESS;
}

