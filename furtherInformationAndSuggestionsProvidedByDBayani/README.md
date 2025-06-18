# Further suggestions, guidance, and information provided by D Bayani with the Flavell Lab in mind.

Please use the following links to navigate to the documents of interest.
- [furtherInformationAndSuggestionsFromDBayani.pdf](https://www.dropbox.com/scl/fi/fzri9hmwpvu7g70xkuoxi/furtherInformationAndSuggestionsFromDBayani.pdf?rlkey=uqt3pmk9iujhvm3o45qrmgbpp&st=i5obv0dr&dl=0)
- [wordsFromDBayani_d9M4y2025tzET.pdf](https://www.dropbox.com/scl/fi/vhj7tpf0go0zw7lu2e86g/wordsFromDBayani_d9M4y2025tzET.pdf?rlkey=ap1y7xkhicrxgbpdlr0g161e3&st=t8qz7wto&dl=0)

The following commands were run on the two PDF documents listed above, and one LibreOffice powerpoint document, "furtherInformationAndSuggestionsFromDBayani.odp", that was used to create the document "furtherInformationAndSuggestionsFromDBayani.pdf" listed above. The file "furtherInformationAndSuggestionsFromDBayani.odp" is not at present shared among the content of this GitHub repository.
Commands used:
```bash
sha512sum $(find . -type f  | sort );
ls -s1 --block-size=1 $(find . -type f | sort );
stat --format=%s\ %n $(find . -type f | sort );
../scripts/getMetadataForAllFiles.sh . ;
```
Following this line is the outcome of running the commands listed above on a folder called "contentShared" which contained only the three aforementioned files:
78b494d2966d988b67e2a4ec30e0df97863dc25f5a4b4af9d67462305f826cadd4bc2deec96b7874b1aaaed4cde8e70c55101f74c508236644e64f3cbd26610e  ./furtherInformationAndSuggestionsFromDBayani.odp
06ec54cdc53aef778e3ccfd77480191af150f23ef6eb94553217268d252daa6834af380d8c7455dd14fe28a9b7b04e6309b34a6b5a1d64a69e9ddca863ffc26b  ./furtherInformationAndSuggestionsFromDBayani.pdf
ff8b1667c9b3488c6708a2096de1e6e217cacf9e19cf9061f72d0ddaebf12fd0197fdc8e5068bc196350e95d3d2ccc72d8dc8501b480d222916495bd42a6ba41  ./wordsFromDBayani_d9M4y2025tzET.pdf
11968512 ./furtherInformationAndSuggestionsFromDBayani.odp
11395072 ./furtherInformationAndSuggestionsFromDBayani.pdf
  282624 ./wordsFromDBayani_d9M4y2025tzET.pdf
11967458 ./furtherInformationAndSuggestionsFromDBayani.odp
11392197 ./furtherInformationAndSuggestionsFromDBayani.pdf
280485 ./wordsFromDBayani_d9M4y2025tzET.pdf
Not_Applicable_Or_Timeout,directory,8,512,4096,2025-06-18 20:59:27.839037113 +0000,1750280367,2025-06-18 21:00:07.035756249 +0000,1750280407,2025-06-18 21:00:06.067819776 +0000,1750280406,2025-06-18 21:00:06.067819776 +0000,1750280406,dd4f520768dafe6990081e74c73c7adff8bdde7f831aa9ea6b8de15d3ed53c7b04eaf15cb332f4ff3b55966b75612bd5c2dd5ca62139eee58470a7f5d59bb62f,dd4f520768dafe6990081e74c73c7adff8bdde7f831aa9ea6b8de15d3ed53c7b04eaf15cb332f4ff3b55966b75612bd5c2dd5ca62139eee58470a7f5d59bb62f
ff8b1667c9b3488c6708a2096de1e6e217cacf9e19cf9061f72d0ddaebf12fd0197fdc8e5068bc196350e95d3d2ccc72d8dc8501b480d222916495bd42a6ba41,regular file,552,512,280485,2025-06-18 21:00:06.067819776 +0000,1750280406,2025-06-18 21:00:57.403420307 +0000,1750280457,2025-06-18 21:00:06.067819776 +0000,1750280406,2025-06-18 21:00:06.067819776 +0000,1750280406,6bed78820ba6a11124d59258bd6b4aaf1015d964e767c852bf69fdbaa4d32f840e0dddf435943844a283e886ca93b2083937031aab819662cc50618d8e41560d,c4669731a03ac621f52bd9ee1e97c09e31d3d6c485437c8ef8ad65c6f34ebe3f805e0cee4ec0f623b7e9bad5389fb7965c66004cb06c5999d4f9876e58b8c4cc
78b494d2966d988b67e2a4ec30e0df97863dc25f5a4b4af9d67462305f826cadd4bc2deec96b7874b1aaaed4cde8e70c55101f74c508236644e64f3cbd26610e,regular file,23376,512,11967458,2025-06-18 20:59:41.229741990 +0000,1750280381,2025-06-18 21:06:14.923566569 +0000,1750280774,2025-06-18 20:59:41.236741366 +0000,1750280381,2025-06-18 20:59:41.236741366 +0000,1750280381,9fd3a44de5bbb10f5001b40645b77b9f5fab7b7e250e1a29ad15ebbc8502015f89a44ddece24bf226a8490a3b68ffd6b026643068daed6af1d6a0feb3d17411c,431e2d23bbd76356fb09a27892754474141d2b4e00b5297dc14293a990496f23b6fb53dfb391c85f5464bcad5d5d96cf653a95477f353e4ab10baf036cb5002e
06ec54cdc53aef778e3ccfd77480191af150f23ef6eb94553217268d252daa6834af380d8c7455dd14fe28a9b7b04e6309b34a6b5a1d64a69e9ddca863ffc26b,regular file,22256,512,11392197,2025-06-18 20:59:41.236741366 +0000,1750280381,2025-06-18 21:00:57.403420307 +0000,1750280457,2025-06-18 20:59:41.240741009 +0000,1750280381,2025-06-18 20:59:41.240741009 +0000,1750280381,4d626be48d11e69b8b3b3e862dcfde15ad2ac9f8bbc36e61c353b36957a7fa6a37a365712c1e28cc1a39a7f0b47808d2c4b87d151f8b7577e21ce34e0c0dd818,5db8aa393a872ea9b1a5ca88164e543e46bc83a9a7fb06caf81d4d2b0d0b47e9ca608a4ba64552f6793882cf032ad49b95881aa58066faf24940ed5d4e68c9c4

